frappe.pages['country-print-select'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Print Format Setup',
		single_column: true
	});

	$(wrapper).find('.page-content').html(`
		<div style="max-width:540px; margin:60px auto; font-family:sans-serif;">

			<div style="text-align:center; margin-bottom:32px;">
				<div style="font-size:48px; margin-bottom:12px;">🖨️</div>
				<h3 style="margin:0; color:var(--heading-color);">Print Format Setup</h3>
				<p style="color:var(--text-muted); margin-top:8px; font-size:14px;">
					Select your country to install the correct print format on this site.
				</p>
			</div>

			<div style="
				background:var(--card-bg);
				border:1px solid var(--border-color);
				border-radius:12px;
				padding:28px;
			">
				<!-- Already Done -->
				<div id="pf-done-msg" style="display:none; text-align:center; padding:16px;">
					<div style="font-size:40px; margin-bottom:12px;">✅</div>
					<h5 style="color:var(--heading-color);">Setup Complete!</h5>
					<p style="color:var(--text-muted); font-size:13px;" id="pf-done-country"></p>
					<a href="/app" class="btn btn-primary btn-sm" style="margin-top:8px;">
						Go to Home →
					</a>
				</div>

				<!-- Setup Form -->
				<div id="pf-setup-form">

					<!-- Country Select -->
					<div style="margin-bottom:20px;">
						<label style="font-weight:600; font-size:13px; color:var(--text-color);">
							🌍 Select Your Country
						</label>
						<select id="pf-country" class="form-control" style="
							margin-top:6px; border-radius:8px;
							padding:10px 14px; font-size:14px;
						">
							<option value="">-- Select Country --</option>
						</select>
						<div id="pf-no-formats-msg" style="
							display:none; margin-top:8px;
							color:var(--text-muted); font-size:12px;
						">
							⚠️ No print formats found for this country.
						</div>
					</div>

					<!-- Format Preview -->
					<div id="pf-preview" style="
						display:none;
						background:var(--highlight-color);
						border-radius:8px;
						padding:14px 16px;
						margin-bottom:20px;
						font-size:13px;
					">
						<div style="color:var(--text-muted); margin-bottom:8px; font-weight:600;">
							📄 Following formats will be installed on this site:
						</div>
						<div id="pf-preview-list"></div>
					</div>

					<!-- Install Button -->
					<div id="pf-action-btns" style="display:none;">
						<button id="pf-install-btn" class="btn btn-primary btn-lg" style="
							width:100%; border-radius:8px;
							font-size:15px; font-weight:600;
							padding:12px;
						">
							⬇️ Install Print Format & Continue
						</button>
					</div>

				</div>
			</div>
		</div>
	`);

	// ── Already done? ─────────────────────────────────────────
	if (frappe.boot.print_format_setup_done) {
		$('#pf-setup-form').hide();
		$('#pf-done-country').text('Country: ' + (frappe.boot.print_format_country || ''));
		$('#pf-done-msg').show();
		return;
	}

	// ── Load countries from Print Format JSON files ───────────
	// We fetch distinct countries from DB (already installed formats)
	// + any country available via API
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype:  'Print Format',
			filters:  [['country', '!=', '']],
			fields:   ['country'],
			limit:    100,
		},
		callback: function(r) {
			if (!r.message || !r.message.length) {
				$('#pf-country').after(
					'<p style="color:red; font-size:12px; margin-top:6px;">' +
					'No countries found. Run after_install first.' +
					'</p>'
				);
				return;
			}

			var countries = [...new Set(r.message.map(d => d.country))].sort();
			countries.forEach(function(c) {
				$('#pf-country').append(`<option value="${c}">${c}</option>`);
			});
		}
	});

	// ── Country change → show formats that will be installed ──
	$('#pf-country').on('change', function() {
		var country = $(this).val();

		$('#pf-preview').hide();
		$('#pf-action-btns').hide();
		$('#pf-no-formats-msg').hide();

		if (!country) return;

		frappe.call({
			method: 'print_format.api.doc.get_formats_available_for_country',
			args: { country: country },
			callback: function(r) {
				if (!r.message || !r.message.length) {
					$('#pf-no-formats-msg').show();
					return;
				}

				var html = r.message.map(function(fmt) {
					var badge = fmt.already_installed
						? '<span style="color:#27ae60; font-size:12px;">✅ Already installed — will update</span>'
						: '<span style="color:#e67e22; font-size:12px;">⬇️ Will be installed</span>';

					return `
						<div style="
							display:flex; justify-content:space-between;
							align-items:center; padding:7px 0;
							border-bottom:1px solid var(--border-color);
						">
							<div>
								<b style="font-size:13px;">${fmt.name}</b>
								<div style="color:var(--text-muted); font-size:12px; margin-top:2px;">
									${fmt.doc_type || '—'}
								</div>
							</div>
							${badge}
						</div>
					`;
				}).join('');

				$('#pf-preview-list').html(html);
				$('#pf-preview').show();
				$('#pf-action-btns').show();
			}
		});
	});

	// ── Install Button ────────────────────────────────────────
	$('#pf-install-btn').on('click', function() {
		var country = $('#pf-country').val();
		if (!country) return;

		var btn = $(this);
		btn.text('Installing...').prop('disabled', true);

		frappe.call({
			method: 'print_format.api.doc.install_print_formats_for_country',
			args: { country: country },
			callback: function(r) {
				btn.html('⬇️ Install Print Format & Continue').prop('disabled', false);

				if (r.message && r.message.success) {
					frappe.boot.print_format_setup_done = true;
					frappe.boot.print_format_country    = country;

					$('#pf-setup-form').hide();
					$('#pf-done-country').text('Country: ' + country);
					$('#pf-done-msg').show();

					frappe.show_alert({
						message:   r.message.message,
						indicator: 'green'
					}, 5);

					setTimeout(function() { frappe.set_route('app'); }, 2000);

				} else {
					frappe.msgprint({
						title:     'Installation Failed',
						message:   r.message ? r.message.message : 'Something went wrong.',
						indicator: 'red'
					});
				}
			}
		});
	});
};
