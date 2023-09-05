import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Criterion
from frappe.utils import get_link_to_form

from hrms.hr.doctype.shift_assignment.shift_assignment import has_overlapping_timings
from hrms.hr.utils import share_doc_with_approver, validate_active_employee, validate_dates,validate_overlap
# from frappe.auth import User


def validate_overlap_(doc):
	existing_records = frappe.get_all(
		"Over Time Application",
		filters={
			 "employee": doc.employee,
			 "date": doc.date,
			 "name": ("!=", doc.name)  # Exclude the current document
		}
	)

	if existing_records:
		frappe.throw("Over Time Application - Overlapping records already exist for the selected date and employee")

	existing_records_ = frappe.get_all(
		"Compensatory Leave Request",
		filters={
			 "employee": doc.employee,
			 "date": doc.date,
			  "docstatus" : 1
		}
	)

	if existing_records_:
		frappe.throw("Compensatory Leave Applied for the Selected Date!")


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


class OverTimeApplication(Document):
	def validate(self):
		validate_active_employee(self.employee)
		validate_dates(self, self.date, self.date)
		validate_overlap_(self)
		# self.validate_from_to_dates("from_date", "to_date")
		# self.validate_overlapping_shift_requests()
		# self.validate_approver()
		# self.validate_default_shift()

	def on_update(self):

		if not self.is_over_time_applicable:
			frappe.throw("You are not allowed to apply for over time!")

		# approvers = get_department_approvers(self.employee)
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

		if not self.is_over_time_applicable:
			frappe.throw("You are not allowed to apply for over time!")

		validate_overlap_(self)

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


			if self.status == 'Approved by Reporting Incharge' or self.status == "Approved by HR" or self.status == "Approved by HOD" or self.status == "Approved by CHO":
				# print("\ndocstatus before submitting---- ",self.docstatus)
				# print("\nstatus before submitting---- ",self.status)

				#  OT Calculation

				frappe.msgprint(
					_("Attendance Application created for Employee: {0}").format(
						frappe.bold(self.employee)
					)
				)

	# def on_cancel(self):
	# 	# print("Cancelling----")
	# 	shift_assignment_list = frappe.get_list(
	# 		"Shift Assignment", {"employee": self.employee, "shift_request": self.name}
	# 	)
	# 	if shift_assignment_list:
	# 		for shift in shift_assignment_list:
	# 			shift_assignment_doc = frappe.get_doc("Shift Assignment", shift["name"])
	# 			shift_assignment_doc.cancel()

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
def get_attendance_in_time_out_time(employee,attendance_date):
	in_time_out_time = frappe.get_value(
		 "Attendance",
		 filters={"employee": employee, "attendance_date": attendance_date,"docstatus":1},
		 fieldname=["in_time","out_time"]
	)
	return in_time_out_time # (datetime.datetime(2023, 5, 3, 7, 26, 31), datetime.datetime(2023, 5, 3, 17, 56, 24))

# ************************* ATTENDANCE STATUS ********************************* #

@frappe.whitelist()
def get_attendance_status(employee,attendance_date):
	attendance_status = frappe.get_value(
		 "Attendance",
		 filters={"employee": employee, "attendance_date": attendance_date,"docstatus":1},
		 fieldname="status"
	)
	return attendance_status


# *************************OVER TIME CALCULATION ********************************* #


from datetime import datetime, timedelta
from hrms.hr.doctype.shift_assignment.shift_assignment import (
	glovis_get_employee_shift,
	glovis_get_shift_details
	)
from hrms.hr.doctype.employee_checkin.employee_checkin import (
	time_diff_in_hours
)
from frappe.utils import get_datetime,get_datetime_str
from hrms.hr.utils import (
	create_additional_leave_ledger_entry,
	get_holiday_dates_for_employee,
	get_leave_period,
	validate_active_employee,
	validate_dates,
	validate_overlap,
)

def custom_round(number):
	if number < 1:
		return 0
	decimal = number - int(number)
	if decimal < 0.5:
		return int(number)
	else:
		return int(number) + 0.5


@frappe.whitelist()
def is_holiday(employee,attendance_date):
	holidays = get_holiday_dates_for_employee(employee, attendance_date, attendance_date)
	# print("holidays----",holidays)

	is_holiday_ = None;
	if len(holidays)>0:
		is_holiday_ = 1
	else:
		is_holiday_ = 0
	return is_holiday_


@frappe.whitelist()
def get_over_time(employee,attendance_date):

	over_time = 0.0

	shift_1_compensatory_days = 0
	shift_2_compensatory_days = 0
	compensatory_days = 0


	attendance_date_time = get_datetime(attendance_date) # it adds time to date 
	
	actual_shift_timings = glovis_get_employee_shift(
		employee, attendance_date_time
	)

	shift_type = actual_shift_timings.shift_type.name

	actual_shift_timings_2 = glovis_get_employee_shift(
		employee, attendance_date_time + timedelta(hours=1)
	)

	shift_type_2 = actual_shift_timings_2.shift_type.name

	attendance_status = get_attendance_status(employee,attendance_date)

	is_holiday_ = is_holiday(employee,attendance_date)

	if is_holiday_:
		if attendance_status == "Present" or attendance_status == "Permission":
			pass
		else:
			frappe.throw("Attendance not found Present or Permission on the selected Date!")
	else:
		if attendance_status == "Present":
			pass
		else:
			frappe.throw("Attendance not found Present on the selected Date!")

	# print("actual_shift_timings---",actual_shift_timings)
	# print("attendance_status---",attendance_status)
	# print("shift_type-----",shift_type)
	# print("shift_type_2---",shift_type_2)

	# Day 1
	GS_SHIFT_DETAILS = glovis_get_shift_details("GS",attendance_date_time)
	A_SHIFT_DETAILS  = glovis_get_shift_details("A",attendance_date_time)
	B_SHIFT_DETAILS  = glovis_get_shift_details("B",attendance_date_time)
	C_SHIFT_DETAILS  = glovis_get_shift_details("C",attendance_date_time)

	# Day 2
	A_SHIFT_DETAILS_2 = glovis_get_shift_details("A",attendance_date_time + timedelta(days=1))

	# Considering OT on weekdays
	if attendance_status == "Present" and is_holiday_ == 0:
		log_start_datetime = None
		log_end_datetime = None
		log_actual_start_datetime = None
		log_actual_end_datetime = None
		ot_shift_2 = None
		shift_1_allowance = 0
		shift_2_allowance = 0

		if shift_type == "GS":
			log_start_datetime = GS_SHIFT_DETAILS.end_datetime
			log_end_datetime = B_SHIFT_DETAILS.end_datetime
			log_actual_start_datetime = log_start_datetime
			log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			ot_shift_1 = "GS"

		elif shift_type == "A":
			log_start_datetime = A_SHIFT_DETAILS.end_datetime
			log_end_datetime = B_SHIFT_DETAILS.end_datetime
			log_actual_start_datetime = log_start_datetime
			log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			ot_shift_1 = "B"

		elif shift_type == "B":
			log_start_datetime = B_SHIFT_DETAILS.end_datetime
			log_end_datetime = C_SHIFT_DETAILS.end_datetime
			log_actual_start_datetime = log_start_datetime
			log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			ot_shift_1 = "C"

		elif shift_type == "C":
			log_start_datetime = C_SHIFT_DETAILS.end_datetime
			log_end_datetime = A_SHIFT_DETAILS_2.end_datetime
			log_actual_start_datetime = log_start_datetime
			log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			ot_shift_1 = "A"

		else:
			frappe.throw("NO Shift Found On The Selected Date!")
	

		
		# print("log_start_datetime---",log_start_datetime)
		# print("log_end_datetime---",log_end_datetime)
		# print("log_actual_end_datetime---",log_actual_end_datetime)


		employee_checkin = frappe.qb.DocType("Employee Checkin")
		query = (
			frappe.qb.from_(employee_checkin)
			.select("*")
			.where(
				(employee_checkin.skip_auto_attendance == 0)
				& (employee_checkin.time.between(log_actual_start_datetime, log_actual_end_datetime))
				& (employee_checkin.employee == employee)
				)
				.orderby("time")
			)
			
		logs = query.run(as_dict=True)

		# print("Employee Checkin---",logs)

		if len(logs)>0:
			last_log = logs[-1]
			time = last_log.time

			if time<log_actual_end_datetime:
				if time>log_end_datetime:
					time = log_end_datetime
					shift_1_allowance = 1
				
				over_time = time_diff_in_hours(log_start_datetime, time)
				over_time = custom_round(over_time)
				
				# for compensatory leaves
				if over_time >= 4:
					shift_1_compensatory_days = 0.5
				if over_time >= 6:
					shift_1_compensatory_days = 1
				#  total compensatory days
				compensatory_days = shift_1_compensatory_days + shift_2_compensatory_days
				


			return over_time, log_start_datetime, time, shift_type, shift_type_2, ot_shift_1, shift_1_allowance,ot_shift_2 ,shift_2_allowance,compensatory_days
		else:
			frappe.throw("No Biometric Records Found On The Select Date!")
		

	# Considering OT on Holidays

	if ((attendance_status == "Present") and (is_holiday_ == 1)):

		if shift_type == "GS":
			ot_shift_1 = "GS"
			log_start_datetime = GS_SHIFT_DETAILS.start_datetime
			log_end_datetime = B_SHIFT_DETAILS.end_datetime
			log_actual_start_datetime = log_start_datetime - timedelta(hours=1)
			log_between_time = GS_SHIFT_DETAILS.end_datetime
			log_actual_end_datetime = log_end_datetime + timedelta(hours=1)

		
		elif shift_type == "A":
			ot_shift_1 = "A"
			# non over-lapping next day shifts so considering OT in 3 shift 
			if shift_type_2 == "A" or shift_type_2 == "B" or shift_type_2 == "C":
				log_start_datetime = A_SHIFT_DETAILS.start_datetime
				log_end_datetime = B_SHIFT_DETAILS.end_datetime
				log_actual_start_datetime = log_start_datetime - timedelta(hours=1)
				log_between_time = A_SHIFT_DETAILS.end_datetime
				log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			

		elif shift_type == "B":
			ot_shift_1 = "B"
			# non over-lapping next day shifts so considering OT in 2 shift 
			if shift_type_2 == "B" or shift_type_2 == "C":
				log_start_datetime = B_SHIFT_DETAILS.start_datetime
				log_end_datetime = C_SHIFT_DETAILS.end_datetime
				log_actual_start_datetime = log_start_datetime - timedelta(hours=1)
				log_between_time = B_SHIFT_DETAILS.end_datetime
				log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			# because of overlapping shifts considering OT in only 1 shift 
			else:
				log_start_datetime = B_SHIFT_DETAILS.start_datetime
				log_end_datetime = B_SHIFT_DETAILS.end_datetime
				log_actual_start_datetime = log_start_datetime - timedelta(hours=1)
				log_between_time = B_SHIFT_DETAILS.end_datetime
				log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
				shift_2_allowance = 0

		elif shift_type == "C":
			ot_shift_1 = "C"
			# non over-lapping next day shifts so considering OT in 1 shift
			if shift_type_2 == "C":
				log_start_datetime = C_SHIFT_DETAILS.start_datetime
				log_end_datetime = A_SHIFT_DETAILS_2.end_datetime
				log_actual_start_datetime = log_start_datetime - timedelta(hours=1)
				log_between_time = C_SHIFT_DETAILS.end_datetime
				log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
			else:
				log_start_datetime = C_SHIFT_DETAILS.start_datetime
				log_end_datetime = C_SHIFT_DETAILS.end_datetime 
				log_actual_start_datetime = log_start_datetime - timedelta(hours=1)
				log_between_time = C_SHIFT_DETAILS.end_datetime
				log_actual_end_datetime = log_end_datetime + timedelta(hours=1)
				shift_2_allowance = 0 
		
		in_time_out_time = get_attendance_in_time_out_time(employee,attendance_date)

		# print("in_time_out_time-----",in_time_out_time)
		in_time = in_time_out_time[0]
		out_time = in_time_out_time[1]
		
		if (not in_time):
			frappe.throw("NO IN Time Record Found on the Selected Date")
		if (not out_time):
			frappe.throw("NO IN Time Record Found on the Selected Date")

		if in_time <= log_start_datetime:
			in_time = log_start_datetime
		
		if log_end_datetime <= out_time:
			out_time = log_end_datetime
		

		employee_checkin = frappe.qb.DocType("Employee Checkin")
		query = (
			frappe.qb.from_(employee_checkin)
			.select("*")
			.where(
				(employee_checkin.skip_auto_attendance == 0)
				& (employee_checkin.time.between(log_actual_start_datetime, log_actual_end_datetime))
				& (employee_checkin.employee == employee)
				)
				.orderby("time")
			)
			
		logs = query.run(as_dict=True)

		# print("Employee Checkin---",logs)

		if len(logs)>1:
			first_log = logs[0]
			last_log = logs[-1]
			first_time = first_log.time
			last_time = last_log.time

			if (
				(log_actual_start_datetime <= first_time <= log_actual_end_datetime)
				and
				(log_actual_start_datetime <= last_time <= log_actual_end_datetime)
			):
				if last_time >log_end_datetime:
					last_time = log_end_datetime
				if first_time < log_start_datetime:
					first_time =  log_start_datetime
				over_time = time_diff_in_hours(first_time,last_time)
				OT_MAX_1 =  time_diff_in_hours(log_start_datetime,log_between_time)
				OT_MAX_2 =  time_diff_in_hours(log_between_time,log_end_datetime)
				if over_time >= OT_MAX_1:
					shift_1_allowance = 1
					if ot_shift_1 == "GS":
						ot_shift_2 = "GS"
					elif ot_shift_1 == "A":
						ot_shift_2 = "B"
					elif ot_shift_1 == "B":
						ot_shift_2 = "C"
					elif ot_shift_1 == "C":
						ot_shift_2 = "A"
				else:
					shift_1_allowance = 0

				#  total compensatory days
				if over_time >= 4:
					shift_1_compensatory_days = 0.5
				if over_time >= 6:
					 shift_1_compensatory_days = 1
				
				# Check wheater OT Shifts are 1 or 2
				if OT_MAX_2 > 2:
					if (over_time >= (OT_MAX_2 + OT_MAX_1)):
						shift_2_allowance = 1
					else:
						shift_2_allowance = 0

					#  total compensatory days
					if (over_time - OT_MAX_1) >= 4:
						shift_2_compensatory_days = 0.5
					if (over_time - OT_MAX_1) >= 6:
						shift_2_compensatory_days = 1

				else:
					ot_shift_2 = None
					shift_2_allowance = 0				
			
				over_time = custom_round(over_time)

				compensatory_days = shift_1_compensatory_days + shift_2_compensatory_days
				compensatory_days = flt(compensatory_days,1)

				return over_time, first_time, last_time, shift_type, shift_type_2 ,ot_shift_1 ,shift_1_allowance ,ot_shift_2 ,shift_2_allowance ,compensatory_days
		
		else:
			frappe.throw("No Sufficient Records Found On The Select Date!")
	
	elif (attendance_status == "Missed Punch"):
		frappe.throw("Please Apply For Missed Punch Application First!")
	
	# print("over_time---",over_time)


# ************************************* TOTAL OVER TIME **************************************** #

from frappe.utils import flt
def calculate_overtime_sum(employee,start_date, end_date):
	overtime_sum = 0
	over_time_qb = frappe.qb.DocType("Over Time Application")

	query = (
		frappe.qb.from_(over_time_qb)
		.select("over_time")
		.where(
			(over_time_qb.docstatus == 1)
			& (over_time_qb.date.between(start_date,end_date))
			& (over_time_qb.employee == employee)
			)
		)
		
	logs = query.run(as_dict=True)

	# print("OT Details----",employee,start_date, end_date)
	# print("OT LOGS----",logs)
	for log in logs:
		overtime_sum += flt(log.over_time)

	return overtime_sum

