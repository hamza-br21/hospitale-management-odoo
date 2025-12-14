/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

// For Odoo 16 compatibility, use the old format
odoo.define(
  "gestion_hospitaliere.dashboard",
  ["require", "web.AbstractAction", "web.core", "web.rpc"],
  function (require) {
    "use strict";

    var AbstractAction = require("web.AbstractAction");
    var core = require("web.core");
    var rpc = require("web.rpc");
    var QWeb = core.qweb;

    var HospitalDashboard = AbstractAction.extend({
      template: "HospitalDashboardMain",

      init: function (parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ["HospitalDashboard"];
      },

      start: function () {
        var self = this;
        return this._super().then(function () {
          self.render_dashboards();
          self.load_dashboard_data();
        });
      },

      render_dashboards: function () {
        var self = this;
        _.each(this.dashboards_templates, function (template) {
          self
            .$(".o_hospital_dashboard")
            .append(QWeb.render(template, { widget: self }));
        });
      },

      load_dashboard_data: function () {
        var self = this;

        // Load KPI data
        rpc
          .query({
            model: "hospital.dashboard",
            method: "search_read",
            args: [
              [],
              [
                "total_patients",
                "total_doctors",
                "total_appointments_today",
                "total_revenue_month",
                "bed_occupancy_rate",
                "total_admissions_active",
              ],
            ],
          })
          .then(function (data) {
            if (data.length > 0) {
              self.update_kpi_cards(data[0]);
            }
          });

        // Load chart data
        this.load_appointment_chart();
        this.load_revenue_chart();
        this.load_department_chart();
      },

      update_kpi_cards: function (data) {
        this.$(".kpi_total_patients .kpi_value").text(data.total_patients || 0);
        this.$(".kpi_total_doctors .kpi_value").text(data.total_doctors || 0);
        this.$(".kpi_appointments_today .kpi_value").text(
          data.total_appointments_today || 0
        );
        this.$(".kpi_revenue_month .kpi_value").text(
          "$" + (data.total_revenue_month || 0).toFixed(2)
        );
        this.$(".kpi_bed_occupancy .kpi_value").text(
          (data.bed_occupancy_rate || 0).toFixed(1) + "%"
        );
        this.$(".kpi_active_admissions .kpi_value").text(
          data.total_admissions_active || 0
        );
      },

      load_appointment_chart: function () {
        var self = this;
        rpc
          .query({
            model: "hospital.dashboard",
            method: "create",
            args: [{}],
          })
          .then(function (dashboard_id) {
            rpc
              .query({
                model: "hospital.dashboard",
                method: "get_appointment_chart_data",
                args: [[dashboard_id]],
              })
              .then(function (data) {
                self.render_appointment_pie_chart(data);
              });
          });
      },

      render_appointment_pie_chart: function (data) {
        var ctx = this.$("#appointmentChart")[0];
        if (!ctx) return;

        // Using Chart.js (you need to include it in your assets)
        if (typeof Chart !== "undefined") {
          new Chart(ctx.getContext("2d"), {
            type: "pie",
            data: {
              labels: ["Draft", "Confirmed", "Done", "Cancelled"],
              datasets: [
                {
                  data: [
                    data.draft || 0,
                    data.confirmed || 0,
                    data.done || 0,
                    data.cancel || 0,
                  ],
                  backgroundColor: ["#fbbf24", "#3b82f6", "#10b981", "#ef4444"],
                },
              ],
            },
            options: {
              responsive: true,
              plugins: {
                legend: {
                  position: "bottom",
                },
                title: {
                  display: true,
                  text: "Appointment Status Distribution",
                },
              },
            },
          });
        }
      },

      load_revenue_chart: function () {
        var self = this;
        rpc
          .query({
            model: "hospital.dashboard",
            method: "create",
            args: [{}],
          })
          .then(function (dashboard_id) {
            rpc
              .query({
                model: "hospital.dashboard",
                method: "get_revenue_chart_data",
                args: [[dashboard_id]],
              })
              .then(function (data) {
                self.render_revenue_line_chart(data);
              });
          });
      },

      render_revenue_line_chart: function (data) {
        var ctx = this.$("#revenueChart")[0];
        if (!ctx || typeof Chart === "undefined") return;

        var months = data.map(function (item) {
          return item.month;
        });
        var revenues = data.map(function (item) {
          return item.revenue;
        });

        new Chart(ctx.getContext("2d"), {
          type: "line",
          data: {
            labels: months,
            datasets: [
              {
                label: "Revenue",
                data: revenues,
                borderColor: "#667eea",
                backgroundColor: "rgba(102, 126, 234, 0.1)",
                tension: 0.4,
                fill: true,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false,
              },
              title: {
                display: true,
                text: "Monthly Revenue Trend",
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function (value) {
                    return "$" + value.toFixed(0);
                  },
                },
              },
            },
          },
        });
      },

      load_department_chart: function () {
        var self = this;
        rpc
          .query({
            model: "hospital.dashboard",
            method: "create",
            args: [{}],
          })
          .then(function (dashboard_id) {
            rpc
              .query({
                model: "hospital.dashboard",
                method: "get_department_patient_distribution",
                args: [[dashboard_id]],
              })
              .then(function (data) {
                self.render_department_bar_chart(data);
              });
          });
      },

      render_department_bar_chart: function (data) {
        var ctx = this.$("#departmentChart")[0];
        if (!ctx || typeof Chart === "undefined") return;

        var departments = data.map(function (item) {
          return item.department;
        });
        var counts = data.map(function (item) {
          return item.count;
        });

        new Chart(ctx.getContext("2d"), {
          type: "bar",
          data: {
            labels: departments,
            datasets: [
              {
                label: "Appointments",
                data: counts,
                backgroundColor: "#764ba2",
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              legend: {
                display: false,
              },
              title: {
                display: true,
                text: "Appointments by Department",
              },
            },
            scales: {
              y: {
                beginAtZero: true,
              },
            },
          },
        });
      },

      on_refresh_dashboard: function (e) {
        e.preventDefault();
        this.load_dashboard_data();
      },
    });

    core.action_registry.add("hospital_dashboard", HospitalDashboard);

    return HospitalDashboard;
  }
);
