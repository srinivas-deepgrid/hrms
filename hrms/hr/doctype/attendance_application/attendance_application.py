
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Criterion
from frappe.utils import get_link_to_form,get_datetime,get_datetime_str

from hrms.hr.doctype.shift_assignment.shift_assignment import has_overlapping_timings
from hrms.hr.utils import share_doc_with_approver, validate_active_employee
from hrms.hr.doctype.shift_assignment.shift_assignment import (
	glovis_get_employee_shift,
	glovis_get_shift_details
	)
from hrms.hr.doctype.employee_checkin.employee_checkin import (
	add_log_based_on_employee_field,
	time_diff_in_hours
)
from datetime import datetime, timedelta
# from frappe.auth import User

def share_doc_with_approver__(doc, user, ptype):
	# if approver does not have permissions, share
	if not frappe.has_permission(doc=doc, ptype=ptype, user=user):
		if ptype == "submit":
			submit = 1
			write = 0
		elif ptype == "write":
			submit = 0
			write  = 1
		frappe.share.add_docshare(
			doc.doctype, doc.name, user, write=write,submit=submit, flags={"ignore_share_permission": True},notify=1
		)

		# frappe.msgprint(
		# 	_("Shared with the user {0} with {1} access").format(user, frappe.bold(ptype), alert=True)
		# )


class OverlappingShiftRequestError(frappe.ValidationError):
	pass


class AttendanceApplication(Document):
	def validate(self):
		validate_active_employee(self.employee)
		self.validate_in_time_out_time()
		# self.validate_from_to_dates("from_date", "to_date")
		# self.validate_overlapping_shift_requests()
		# self.validate_approver()
		# self.validate_default_shift()

	def validate_in_time_out_time(self):
		if self.previous_attendance_status not in ["Missed Punch","Permission"]:
			frappe.throw("Previous Attendance Status Should be Missed Punch/Permission")
		if self.in_time > self.out_time:
			frappe.throw("IN Time Should be less than OUT Time")
		if self.employee and self.date and self.shift and self.in_time and self.out_time:
			SHIFT_DETAILS = glovis_get_shift_details(self.shift,get_datetime(self.date))
			# print("SHIFT_DETAILS---",SHIFT_DETAILS,"\n",datetime.strptime(self.in_time, "%Y-%m-%d %H:%M:%S"))
			in_time = datetime.strptime(self.in_time, "%Y-%m-%d %H:%M:%S") 
			out_time = datetime.strptime(self.out_time, "%Y-%m-%d %H:%M:%S")
			if (
				(SHIFT_DETAILS.actual_start <= in_time <= SHIFT_DETAILS.actual_end)
				and
				(SHIFT_DETAILS.actual_start <= out_time <= SHIFT_DETAILS.actual_end)
			):
				working_hours = time_diff_in_hours(in_time ,out_time)
				print('working_hours----',working_hours)
				if self.current_attendance_status == "Half Day":
					if working_hours < 4:
						frappe.throw(_("For Half Day - Status Minimum Working Hours Should be 4Hrs"))
				elif self.current_attendance_status == "Absent":
					if working_hours > 4:
						frappe.throw(_("For Absent - Status Maximum Working Hours Should be 4Hrs"))
			else:
				frappe.throw(_("Please select In Time and Out Time within {0} and {1} Period").format(frappe.bold(SHIFT_DETAILS.actual_start),frappe.bold(SHIFT_DETAILS.actual_end)))

	def on_update(self):

		# approvers = get_department_approvers(self.employee)
		self.validate_in_time_out_time()
		user_roles = frappe.get_user().get_roles()
		# print("user_roles----",user_roles)
		hr_roles = ["HR User", "HR Manager"]
		
	
		name = frappe.get_user().name
		# frappe.user.name doesn't work
		# print("name--0--",name)

		# check whether approver has right to Approve Approval
		isApprover = (name == self.approver) or (name == self.hod_approver) or (name == self.cho_approver)
		# print("isApprover---",isApprover,"\n",self.approver,"\n",self.hod_approver)

		if self.request_action == 'Draft':
			# if Reporting Incharge Exists
			if (
				self.approver
				and
				self.status == 'Awaiting Reporting Incharge Approval'
				and
				self.reporting_incharge_status == 'Awaiting Reporting Incharge Approval'
			):
				# if HOD Exists
				if self.hod_approver:
					#  Share Doc to Repoting Incharge for Level-1 Approval
					share_doc_with_approver__(self,self.approver,"write")
					frappe.msgprint(_("Sent to Reporting Incharge {0} to Approve").format(frappe.bold(self.approver)))
				# if HOD Doesn't Exists
				else:
					# Share doc to Reporting Incharge for Direct Approval
					share_doc_with_approver__(self,self.approver,"submit")
					frappe.msgprint(_("Directly Sent to Reporting Incharge {0} to Approve").format(frappe.bold(self.approver)))
			# if Reporting Incharge Doesn't Exists
			else:
				# if HOD Exists
				if (
					self.hod_approver
					and
					self.status ==  'Awaiting HOD Approval'
					and
					self.hod_approver_status == 'Awaiting HOD Approval'
				):
					# Share doc to HOD for Direct Approval
					share_doc_with_approver__(self,self.hod_approver,"submit")
					frappe.msgprint(_("Directly Sent to HOD {0} to Approve").format(frappe.bold(self.hod_approver)))
				# if HOD Doesn't Exists
				elif(
					(not self.hod_approver)
					and 
					self.cho_approver
					and 
					self.status ==  'Awaiting CHO Approval'
					and
					self.cho_approver_status == 'Awaiting CHO Approval'
				):
					# Share doc to CHO for Direct Approval
					share_doc_with_approver__(self,self.cho_approver,"submit")
					frappe.msgprint(_("Diectly Sent to CHO {0} to Approve").format(frappe.bold(self.cho_approver)))
				else:
					# NO Approvers
					frappe.throw("There are no Approvers Assigned to Approve")

			
		elif self.request_action == 'Approved' and isApprover:
			# if Reporting Incharge Exists and Reporting Incharge is the current Approver
			if self.approver and (self.approver == name):
				# if HOD Exists
				if (
					self.hod_approver
					and 
					self.status == 'Awaiting HOD Approval'
					and
					self.reporting_incharge_status == 'Approved by Reporting Incharge'
					and
					self.hod_approver_status == 'Awaiting HOD Approval'
				):
					#  Share Doc to HOD for Level-2 Approval
					share_doc_with_approver__(self,self.hod_approver,"submit")
					frappe.msgprint(_("Sent to HOD {0} for Final Approval").format(frappe.bold(self.hod_approver)))
				# if HOD Doesn't Exists - Reporting Incharge is doing Final Approval 
				elif(
					self.status == 'Approved by Reporting Incharge'
					and
					self.reporting_incharge_status == 'Approved by Reporting Incharge'
				):
					frappe.msgprint(_("Approved by Reporting Incharge {0}").format(frappe.bold(self.approver)))
			
			# if HOD Exists and HOD is the current Approver then HOD will be the Final Approver
			elif(
				self.hod_approver 
				and 
				(self.hod_approver == name)
				and
				self.status == 'Approved by HOD'
				and
				self.hod_approver_status == 'Approved by HOD'
			):
				frappe.msgprint(_("Approved by HOD {0}").format(frappe.bold(self.hod_approver)))
				
			# if CHO Exists and CHO is the current Approver then CHO will be the Final Approver
			elif(
				self.cho_approver 
				and 
				(self.cho_approver == name)
				and
				self.status == 'Approved by CHO'
				and
				self.cho_approver_status == 'Approved by CHO'
			):
				frappe.msgprint(_("Approved by CHO {0}").format(frappe.bold(self.cho_approver)))
				
		
		elif self.request_action == 'Rejected' and isApprover:
			# if Reporting Incharge Exists and Reporting Incharge is the current Approver
			if (
				self.approver 
				and 
				(self.approver == name)
				and
				self.status == 'Rejected by Reporting Incharge'
				and
				self.reporting_incharge_status == 'Rejected by Reporting Incharge'
			):
				# if HOD Exists
				if self.hod_approver:
					#  Get back  Doc from HOD which went for Level-2 Approval
					if frappe.has_permission(doc=self, ptype="submit", user=self.hod_approver):
						frappe.share.add_docshare(
							self.doctype, self.name, self.hod_approver,read=0,submit=0, flags={"ignore_share_permission": True},notify=1
							)
					frappe.msgprint(_("Request is got Rejected by reporting Incharge {0}").format(frappe.bold(self.approver)))
				# if HOD Doesn't Exists - Reporting Incharge is doing Final Approval 
				else:
					frappe.msgprint(_("Request is got Rejected by reporting Incharge {0}").format(frappe.bold(self.approver)))
			
			# if HOD Exists and HOD is the current Approver then HOD will be the Final Approver
			elif(
				self.hod_approver 
				and 
				(self.hod_approver == name)
				and
				self.status == 'Rejected by HOD'
				and
				self.hod_approver_status == 'Rejected by HOD'
			):
				frappe.msgprint(_("Request is got Rejected by HOD {0}").format(frappe.bold(self.hod_approver)))
				
			# if CHO Exists and CHO is the current Approver then CHO will be the Final Approver
			elif(
				self.cho_approver 
				and 
				(self.cho_approver == name)
				and
				self.status == 'Rejected by CHO'
				and
				self.cho_approver_status == 'Rejected by CHO'
			):
				frappe.msgprint(_("Request is got Rejected by CHO {0}").format(frappe.bold(self.cho_approver)))
				
		elif any(role in user_roles for role in hr_roles):
			if self.request_action == 'Approved' and self.status == 'Approved by HR':
				frappe.msgprint(_("Approved by HR {0}").format(frappe.bold(name)))
			elif self.request_action == 'Rejected' and self.status == 'Rejected by HR':
				frappe.msgprint(_("Rejected by HR {0}").format(frappe.bold(name)))
			else:
				frappe.throw("Something went wrong HR")
		
		else:
			frappe.throw("You are not allowed to Edit")

			
			
		
	def on_submit(self):

		userid = frappe.db.get_value("Employee",self.employee,'user_id')
		name = frappe.get_user().name
		# print("userid----name",userid,name)

		if name == userid: #self Approver
			# print("Self Approval is not Allowed!")
			frappe.throw("Self Approval is not Allowed!")
		else: #if Approver and 	Applier are not equal
			# print("Applier and Approver are not equal")
			if self.status not in [
				"Approved", 
				"Rejected",
				"Approved by HR",
				"Rejected by HR",
				"Approved by CHO",
				"Rejected by CHO",
				"Approved by Reporting Incharge",
				"Rejected by Reporting Incharge",
				"Approved by HOD",
				"Rejected by HOD",
				"Awaiting Reporting Incharge Approval",
				"Awaiting HOD Approval",
				"Awaiting HR Approval",
				"Draft"
				]:
				frappe.throw(_("Only Shift Request with other status can't be submitted"))

			if self.request_action == "Draft":
				frappe.throw(_("Please select Request action Approve or Reject"))

			if self.current_attendance_status not in ["Present","Work From Home","Half Day","Absent"]:
				frappe.throw(_("Current Attendance Status Should be Present / Work From Home / Half Day / Absent"))

			if self.status == 'Approved by Reporting Incharge' or self.status == "Approved by HR" or self.status == "Approved by HOD" or self.status == "Approved by CHO":
				# print("\ndocstatus before submitting---- ",self.docstatus)
				# print("\nstatus before submitting---- ",self.status)

				# Creating Employee Checks Ins before Approval

				if (
					(self.in_time == self.previous_in_time)
					or
					(self.in_time == self.previous_out_time)
				):
					pass
				else:
					# print("Adding in time")
					add_log_based_on_employee_field(
						employee_field_value = self.employee,
						timestamp = self.in_time,
						skip_auto_attendance=0,
						employee_fieldname="employee",
						status = 'Attendance Application'
						)

				if (
					(self.out_time == self.previous_in_time)
					or
					(self.out_time == self.previous_out_time)
				):
					pass
				else:
					# print("Adding out time")
					add_log_based_on_employee_field(
						employee_field_value = self.employee,
						timestamp = self.out_time,
						skip_auto_attendance=0,
						employee_fieldname="employee",
						status = 'Attendance Application'
						)

				count = 0

				if self.current_attendance_status == "Present" or self.current_attendance_status == "Work From Home":
					count = 1
				elif self.current_attendance_status == "Half Day":
					count = 0.5
				elif self.current_attendance_status == "Absent":
					count = 0	
				
				frappe.db.set_value("Attendance", {"employee": self.employee, "attendance_date": self.date,"docstatus":1}, {
					"status": self.current_attendance_status,
					"in_time": self.in_time,
					"out_time": self.out_time,
					"count" : count
					}
				)


				frappe.msgprint(
					_("Attendance Application created for Employee: {0}").format(
						frappe.bold(self.employee)
					)
				)

	def on_cancel(self):
		if doc.docstatus == 2:
			frappe.db.set_value("Attendance", {"employee": self.employee, "attendance_date": self.date,"docstatus":1}, {
					"docstatus",2
					}
				)


	def validate_default_shift(self):
		#  have to implement 
		default_shift = frappe.get_value("Employee", self.employee, "default_shift")
		if self.shift_type == default_shift:
			frappe.throw(
				_("You can not request for your Default Shift: {0}").format(frappe.bold(self.shift_type))
			)

	def validate_approver(self):
		approvers = get_department_approvers(self.employee)
		# print("******* validate_approver *****",approvers,"\n\n",self.approver)

		# if self.approver not in approvers:
		# 	frappe.throw(_("Only Approvers can Approve this Request."))
		
		

	def validate_overlapping_shift_requests(self):
		overlapping_dates = self.get_overlapping_dates()

		# print("overlapping_dates-----",overlapping_dates)

		if len(overlapping_dates):
			self.throw_overlap_error(overlapping_dates[0])
			# if dates are overlapping, check if timings are overlapping, else allow
			# overlapping_timings = has_overlapping_timings(self.shift_type, overlapping_dates[0].shift_type)
			# if overlapping_timings:
			# 	self.throw_overlap_error(overlapping_dates[0])

	def get_overlapping_dates(self):
		# print("self.name---",self.name)
		if not self.name:
			self.name = "New Shift Request"

		shift = frappe.qb.DocType("Shift Request")
		status_list = [
			"Approved by HR",
			"Approved by Reporting Incharge",
			"Approved by HOD",
			"Approved by CHO"
		]
		query = (
			frappe.qb.from_(shift)
			.select(shift.name, shift.shift_type)
			.where((shift.employee == self.employee) & (shift.docstatus < 2) & (shift.name != self.name) & shift.status.isin(status_list))
		)

		if self.to_date:
			query = query.where(
				Criterion.any(
					[
						Criterion.any(
							[
								shift.to_date.isnull(),
								((self.from_date >= shift.from_date) & (self.from_date <= shift.to_date)),
							]
						),
						Criterion.any(
							[
								((self.to_date >= shift.from_date) & (self.to_date <= shift.to_date)),
								shift.from_date.between(self.from_date, self.to_date),
							]
						),
					]
				)
			)
		else:
			query = query.where(
				shift.to_date.isnull()
				| ((self.from_date >= shift.from_date) & (self.from_date <= shift.to_date))
			)

		return query.run(as_dict=True)

	def throw_overlap_error(self, shift_details):
		shift_details = frappe._dict(shift_details)
		msg = _(
			"Employee {0} has already applied for Shift {1}: {2} that overlaps within this period"
		).format(
			frappe.bold(self.employee),
			frappe.bold(shift_details.shift_type),
			get_link_to_form("Shift Request", shift_details.name),
		)

		frappe.throw(msg, title=_("Overlapping Shift Requests"), exc=OverlappingShiftRequestError)


@frappe.whitelist()
def get_department_approvers(employee):
	# print("Employee----",employee)
	department = frappe.get_value("Employee", employee, "department")
	shift_approver = frappe.get_value("Employee",employee, "shift_request_approver")
	approvers = frappe.db.sql(
		"""select approver from `tabDepartment Approver` where parent= %s and parentfield = 'shift_request_approver'""",
		(department),
	)
	# print("---------approvers----0",approvers) #(('clintonlourthuraj@gmail.com',),)
	approvers = [approver[0] for approver in approvers]
	# print("---------approvers----1",approvers)
	approvers.insert(0,shift_approver)
	# print("---------approvers----2",approvers)
	return approvers

# ************************* ATTENDANCE IN TIME OUT TIME ********************************* #

@frappe.whitelist()
def get_attendance_in_time_out_time_shift(employee,attendance_date):
	in_time_out_time = frappe.get_value(
		 "Attendance",
		 filters={"employee": employee, "attendance_date": attendance_date,"docstatus":1},
		 fieldname=["in_time","out_time","shift"]
	)
	return in_time_out_time # (datetime.datetime(2023, 5, 3, 7, 26, 31), datetime.datetime(2023, 5, 3, 17, 56, 24),..GS..)

# ************************* ATTENDANCE STATUS ********************************* #

@frappe.whitelist()
def get_attendance_status(employee,attendance_date):
	attendance_status = frappe.get_value(
		 "Attendance",
		 filters={"employee": employee, "attendance_date": attendance_date,"docstatus":1},
		 fieldname="status"
	)
	return attendance_status
