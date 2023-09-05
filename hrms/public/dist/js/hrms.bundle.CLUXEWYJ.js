(() => {
  // frappe-html:/home/hrms/frappe-bench/apps/hrms/hrms/public/js/templates/employees_to_mark_attendance.html
  frappe.templates["employees_to_mark_attendance"] = `{% if data.length %}
<div class="col-md-12 col-xs-12">
	<div class="col-md-12 col-xs-12" style="padding-bottom:15px;">
		<b>Employees to mark attendance</b>
	</div>
	{% for item in data %}
	<div class="col-md-4 col-xs-6" style="padding-bottom:10px;">
		{{ item.employee }} &nbsp;&nbsp; {{ item.employee_name }}
	</div>
	{% } %}
</div>
{% } else { %}
<div class="col-md-12 col-xs-12">
	<div class="col-md-12 col-xs-12" style="padding-bottom:15px;">
		<b> Attendance records not found </b>
	</div>
</div>
{% } %}
`;

  // ../hrms/hrms/public/js/utils.js
  frappe.provide("hrms");
  frappe.provide("hrms.utils");
  $.extend(hrms, {
    proceed_save_with_reminders_frequency_change: () => {
      frappe.ui.hide_open_dialog();
      frappe.call({
        method: "hrms.hr.doctype.hr_settings.hr_settings.set_proceed_with_frequency_change",
        callback: () => {
          cur_frm.save();
        }
      });
    }
  });
})();
//# sourceMappingURL=hrms.bundle.CLUXEWYJ.js.map
