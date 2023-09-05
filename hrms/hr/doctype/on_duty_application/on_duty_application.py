import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, getdate

from erpnext.setup.doctype.employee.employee import is_holiday

from hrms.hr.utils import validate_active_employee, validate_dates


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

class OnDutyApplication(Document):
	def validate(self):
		validate_active_employee(self.employee)
		validate_dates(self, self.from_date, self.to_date)

	def on_update(self):
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

				#  Logic
				self.create_attendance()

	def on_cancel(self):
		attendance_list = frappe.get_list(
			"Attendance", {"employee": self.employee, "on_duty_application": self.name}
		)
		if attendance_list:
			for attendance in attendance_list:
				attendance_obj = frappe.get_doc("Attendance", attendance["name"])
				attendance_obj.cancel()

	def create_attendance(self):
		request_days = date_diff(self.to_date, self.from_date) + 1
		for number in range(request_days):
			attendance_date = add_days(self.from_date, number)
			skip_attendance = self.validate_if_attendance_not_applicable(attendance_date)
			if not skip_attendance:
				attendance = frappe.new_doc("Attendance")
				attendance.employee = self.employee
				attendance.employee_name = self.employee_name
				attendance.status = "Present"
				attendance.attendance_date = attendance_date
				attendance.company = self.company
				attendance.on_duty_application = self.name
				attendance.count = 1
				attendance.save(ignore_permissions=True)
				attendance.submit()

	def validate_if_attendance_not_applicable(self, attendance_date):
		# Check if attendance_date is a Holiday
		if is_holiday(self.employee, attendance_date):
			frappe.msgprint(
				_("Attendance not submitted for {0} as it is a Holiday.").format(attendance_date), alert=1
			)
			return True

		# Check if employee on Leave
		leave_record = frappe.db.sql(
			"""select half_day from `tabLeave Application`
			where employee = %s and %s between from_date and to_date
			and docstatus = 1""",
			(self.employee, attendance_date),
			as_dict=True,
		)
		if leave_record:
			frappe.msgprint(
				_("Attendance not submitted for {0} as {1} on leave.").format(attendance_date, self.employee),
				alert=1,
			)
			return True

		return False

