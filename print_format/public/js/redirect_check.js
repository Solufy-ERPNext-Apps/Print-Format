
// frappe.provide("erpnext.setup");

function check_and_redirect() {
    try {
        if (!frappe.boot) return;
        if (frappe.boot.print_format_setup_done) return;

        if (!frappe.session) return;
        if (frappe.session.user === 'Guest') return;
        if (!frappe.user.has_role('System Manager')) return;

        var route = frappe.get_route();
        if (!route) return;
        if (route[0] === 'country-print-select') return;
        if (route[0] === 'login') return;

        frappe.set_route('country-print-select');

    } catch(e) {
    }
}

// // $(document).on('page-change', function () {
// //     check_and_redirect();
// // });


$(document).on("setup_wizard_complete", function() {
		check_and_redirect();
});


// frappe.setup.on("after_complete", function() {
//     window.location.href = "/app/country-print-select";
// });
// if (window.location.pathname.indexOf('setup-wizard') !== -1) {
//     localStorage.setItem('current_route', '/app/country-print-select');
// }
