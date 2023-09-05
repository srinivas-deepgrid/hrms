(() => {
  // ../hrms/hrms/public/js/performance/performance_feedback.js
  frappe.provide("hrms");
  hrms.PerformanceFeedback = class PerformanceFeedback {
    constructor({ frm, wrapper }) {
      this.frm = frm;
      this.wrapper = wrapper;
    }
    refresh() {
      this.prepare_dom();
      this.setup_feedback_view();
    }
    prepare_dom() {
      this.wrapper.find(".feedback-section").remove();
    }
    setup_feedback_view() {
      frappe.run_serially([
        () => this.get_feedback_history(),
        (data) => this.render_feedback_history(data),
        () => this.setup_actions()
      ]);
    }
    get_feedback_history() {
      let me = this;
      return new Promise((resolve) => {
        frappe.call({
          method: "hrms.hr.doctype.appraisal.appraisal.get_feedback_history",
          args: {
            employee: me.frm.doc.employee,
            appraisal: me.frm.doc.name
          }
        }).then((r) => resolve(r.message));
      });
    }
    async render_feedback_history(data) {
      const { feedback_history, reviews_per_rating, avg_feedback_score } = data || {};
      const can_create = await this.can_create();
      const feedback_html = frappe.render_template("performance_feedback_history", {
        feedback_history,
        average_feedback_score: avg_feedback_score,
        reviews_per_rating,
        can_create
      });
      $(this.wrapper).empty();
      $(feedback_html).appendTo(this.wrapper);
    }
    setup_actions() {
      let me = this;
      $(".new-feedback-btn").click(() => {
        me.add_feedback();
      });
    }
    add_feedback() {
      frappe.run_serially([
        () => this.get_feedback_criteria_data(),
        (criteria_data) => this.show_add_feedback_dialog(criteria_data)
      ]);
    }
    get_feedback_criteria_data() {
      let me = this;
      return new Promise((resolve) => {
        frappe.db.get_doc("Appraisal Template", me.frm.doc.appraisal_template).then(({ rating_criteria }) => {
          const criteria_list = [];
          rating_criteria.forEach((entry) => {
            criteria_list.push({
              "criteria": entry.criteria,
              "per_weightage": entry.per_weightage
            });
          });
          resolve(criteria_list);
        });
      });
    }
    show_add_feedback_dialog(criteria_data) {
      let me = this;
      const dialog = new frappe.ui.Dialog({
        title: __("Add Feedback"),
        fields: me.get_feedback_dialog_fields(criteria_data),
        primary_action: function() {
          const data = dialog.get_values();
          frappe.call({
            method: "add_feedback",
            doc: me.frm.doc,
            args: {
              feedback: data.feedback,
              feedback_ratings: data.feedback_ratings
            },
            freeze: true,
            callback: function(r) {
              var _a, _b;
              if (!r.exc) {
                frappe.run_serially([
                  () => me.frm.refresh_fields(),
                  () => me.refresh()
                ]);
                frappe.show_alert({
                  message: __("Feedback {0} added successfully", [(_b = (_a = r.message) == null ? void 0 : _a.name) == null ? void 0 : _b.bold()]),
                  indicator: "green"
                });
              }
              dialog.hide();
            }
          });
        },
        primary_action_label: __("Submit")
      });
      dialog.show();
    }
    get_feedback_dialog_fields(criteria_data) {
      return [
        {
          label: "Feedback",
          fieldname: "feedback",
          fieldtype: "Text Editor",
          reqd: 1,
          enable_mentions: true
        },
        {
          label: "Feedback Rating",
          fieldtype: "Table",
          fieldname: "feedback_ratings",
          cannot_add_rows: true,
          data: criteria_data,
          fields: [
            {
              fieldname: "criteria",
              fieldtype: "Link",
              in_list_view: 1,
              label: "Criteria",
              options: "Employee Feedback Criteria",
              reqd: 1
            },
            {
              fieldname: "per_weightage",
              fieldtype: "Percent",
              in_list_view: 1,
              label: "Weightage"
            },
            {
              fieldname: "rating",
              fieldtype: "Rating",
              in_list_view: 1,
              label: "Rating"
            }
          ]
        }
      ];
    }
    async can_create() {
      var _a, _b;
      const is_employee = ((_b = (_a = await frappe.db.get_value("Employee", { "user_id": frappe.session.user }, "name")) == null ? void 0 : _a.message) == null ? void 0 : _b.name) || false;
      return is_employee && frappe.model.can_create("Employee Performance Feedback");
    }
  };

  // frappe-html:/home/hrms/frappe-bench/apps/hrms/hrms/public/js/templates/performance_feedback_history.html
  frappe.templates["performance_feedback_history"] = `<div class="feedback-section col-xs-12">
	{% if (feedback_history.length) { %}
		<div class="feedback-summary mb-5">
			{%= frappe.render_template("performance_feedback_summary",
					{
						number_of_stars: 5,
						average_rating: average_feedback_score,
						feedback_count: feedback_history.length,
						reviews_per_rating: reviews_per_rating
					}
				)
			%}
		</div>
	{% } %}

	{% if (can_create) { %}
		<div class="new-btn pb-3 text-right">
			<button class="new-feedback-btn btn btn-sm d-inline-flex align-items-center justify-content-center px-3 py-2">
				<svg class="icon icon-sm">
					<use href="#icon-add"></use>
				</svg>
				{{ __("New Feedback") }}
			</button>
		</div>
	{% } %}

	<div class="feedback-history mb-3">
		{% if (feedback_history.length) { %}
			{% for (let i=0, l=feedback_history.length; i<l; i++) { %}
				<div class="feedback-content p-3 d-flex flex-row mt-3" data-name="{{ feedback_history[i].name }}">
					<div class="reviewer-info mb-2 col-xs-3">
						<div class="row">
							<div class="col-xs-2">
								{{ frappe.avatar(feedback_history[i].user, "avatar-medium") }}
							</div>
							<div class="col-xs-10">
								<div class="ml-2">
									<div class="title font-weight-bold">
										{{ strip_html(feedback_history[i].reviewer_name) }}
									</div>
									{% if (feedback_history[i].reviewer_designation) { %}
										<div class="small text-muted">
											{{ strip_html(feedback_history[i].reviewer_designation) }}
										</div>
									{% } %}
								</div>
							</div>
						</div>
					</div>

					<div class="reviewer-feedback col-xs-6">
						<div class="rating">
							{%= frappe.render_template("rating",
									{number_of_stars: 5, average_rating: feedback_history[i].total_score, for_summary: false}
								)
							%}
						</div>
						<div class="feedback my-3">
							{{ feedback_history[i].feedback }}
						</div>
					</div>

					<div class="feedback-info col-xs-3 d-flex flex-row justify-content-end align-items-baseline">
						<div class="time small text-muted mr-2">
							{{ frappe.datetime.comment_when(feedback_history[i].added_on) }}
						</div>
						<a
							href="{{ frappe.utils.get_form_link("Employee Performance Feedback", feedback_history[i].name) }}"
							title="{{ __("Open Feedback") }}">
							<svg class="icon icon-sm">
								<use href="#icon-link-url" class="like-icon"></use>
							</svg>
						</a>
					</div>
				</div>
			{% } %}
		{% } else { %}
			<div class="no-feedback d-flex flex-col justify-content-center align-items-center text-muted">
				<span>{{ __("This employee has not received any feedback yet") }}</span>
			</div>
		{% } %}
	</div>
</div>
`;

  // frappe-html:/home/hrms/frappe-bench/apps/hrms/hrms/public/js/templates/performance_feedback_summary.html
  frappe.templates["performance_feedback_summary"] = `<div class="feedback-summary-section my-4 d-flex">
	<div class="rating-summary-numbers col-3">
		<h2 class="average-rating">{{ average_rating }}</h2>
		<div class="feedback-count mb-2">
			{{ cstr(feedback_count)}} {{ feedback_count > 1 ? __("reviews") : __("review") }}
		</div>

		<!-- Ratings Summary -->
		{%= frappe.render_template("rating",
				{number_of_stars: number_of_stars, average_rating: average_rating, for_summary: true}
			)
		%}

		<div class="mt-2">{{ cstr(average_rating) + " " + __("out of") + " " }} {{number_of_stars}}</div>
	</div>

	<!-- Rating Progress Bars -->
	<div class="rating-progress-bar-section col-4 ml-4">
		{% for(let i=0, l=reviews_per_rating.length; i<l; i++) { %}
			<div class="col-sm-4 small rating-bar-title">
				{{ i+1 }} star
			</div>
			<div class="row">
				<div class="col-md-7">
					<div class="progress rating-progress-bar" title="{{ reviews_per_rating[i] }} % of reviews are {{ i+1 }} star">
						<div class="progress-bar progress-bar-cosmetic" role="progressbar"
							aria-valuenow="{{ reviews_per_rating[i] }}"
							aria-valuemin="0" aria-valuemax="100"
							style="width: {{ reviews_per_rating[i] }}%;">
						</div>
					</div>
				</div>
				<div class="col-sm-1 small">
					{{ reviews_per_rating[i] }}%
				</div>
			</div>
		{% } %}
	</div>
</div>
`;

  // frappe-html:/home/hrms/frappe-bench/apps/hrms/hrms/public/js/templates/rating.html
  frappe.templates["rating"] = `<div class="d-flex flex-col">
	<div class="rating {{ for_summary ? 'ratings-pill' : ''}}">
		{% for (let i = 1; i <= number_of_stars; i++) { %}
			{% if (i <= average_rating) { %}
				{% right_class = 'star-click'; %}
			{% } else { %}
				{% right_class = ''; %}
			{% } %}

			{% if ((i <= average_rating) || ((i - 0.5) == average_rating)) { %}
				{% left_class = 'star-click'; %}
			{% } else { %}
				{% left_class = ''; %}
			{% } %}

			<svg class="icon icon-md" data-rating={{i}} viewBox="0 0 24 24" fill="none">
				<path class="right-half {{ right_class }}" d="M11.9987 3.00011C12.177 3.00011 12.3554 3.09303 12.4471 3.27888L14.8213 8.09112C14.8941 8.23872 15.0349 8.34102 15.1978 8.3647L20.5069 9.13641C20.917 9.19602 21.0807 9.69992 20.7841 9.9892L16.9421 13.7354C16.8243 13.8503 16.7706 14.0157 16.7984 14.1779L17.7053 19.4674C17.7753 19.8759 17.3466 20.1874 16.9798 19.9945L12.2314 17.4973C12.1586 17.459 12.0786 17.4398 11.9987 17.4398V3.00011Z" fill="var(--star-fill)" stroke="var(--star-fill)"/>
				<path class="left-half {{ left_class }}" d="M11.9987 3.00011C11.8207 3.00011 11.6428 3.09261 11.5509 3.27762L9.15562 8.09836C9.08253 8.24546 8.94185 8.34728 8.77927 8.37075L3.42887 9.14298C3.01771 9.20233 2.85405 9.70811 3.1525 9.99707L7.01978 13.7414C7.13858 13.8564 7.19283 14.0228 7.16469 14.1857L6.25116 19.4762C6.18071 19.8842 6.6083 20.1961 6.97531 20.0045L11.7672 17.5022C11.8397 17.4643 11.9192 17.4454 11.9987 17.4454V3.00011Z" fill="var(--star-fill)" stroke="var(--star-fill)"/>
			</svg>
		{% } %}
	</div>
	{% if (!for_summary) { %}
		<p class="ml-3" style="line-height: 2;">
			({{ average_rating }})
		</p>
	{% } %}
</div>
`;
})();
//# sourceMappingURL=performance.bundle.IIOPSYNA.js.map
