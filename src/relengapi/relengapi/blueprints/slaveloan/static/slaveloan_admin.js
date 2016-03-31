function reload_loans() {
    $('#loans-table tbody').empty();
    $.ajax({
        url: _get_loans_url,
        dataType: 'json',
        success: function(data) {
            $.each(data.result,function(i,row){
                row_html = $('<tr>')
                row_html.append(
                    $('<td>').append(
                        $('<a>').attr("href", _details_url_prefix.replace('/0', '/'+row.id)).text(row.id)
                    ),
                    $('<td>').append(
                        row.bug_id ?
                        $('<a>').attr("href", 'https://bugzil.la/' + row.bug_id).text(row.bug_id)
                        : "&lt;none&gt;"
                    ),
                    $('<td>').text(row.status),
                    $('<td>').text(row.human.ldap_email),
                    $('<td>').text(row.human.bugzilla_email)
                );
                if (row.machine) {
                    row_html.append(
                        $('<td>').text(row.machine.fqdn),
                        $('<td>').text(row.machine.ipaddress)
                    )
                } else {
                    row_html.append($('<td>'), $('<td>'))
                }
                row_html.appendTo('#loans-table tbody');
            });
        }
    });
}

$(reload_loans);

$(function() {
    var form = $('form#new-loan');
    var button = form.find('#submit_loan');
    button.click(function() {
        /* disable the button to prevent double issues */
        button.prop('disabled', true);

        var good = function(loanid) {
            reload_loans();
            alertify.success("Loan creation successful (id: " + loanid + ")");
            form[0].reset(); // Converts to native JS DOM first
            /* re-enable the button so we can submit a loan again */
            button.prop('disabled', false);
        };
        var bad = function(errmsg) {
            /* re-enable the button so users can try again */
            button.prop('disabled', false);
            alertify.error(errmsg);
        };

        var form_status = form.find('select[name=status]').val();
        var form_bug_id = form.find('input[name=bug_id]').val();
        var form_ldap = form.find('input[name=ldap_email]').val();
        var form_bmo = form.find('input[name=bugzilla_email]').val();
        var form_fqdn = form.find('input[name=fqdn]').val();
        var form_ipaddress = form.find('input[name=ipaddress]').val();
        if (!form_status) {
            bad('Status is empty, how did that happen?');
            return;
        }
        if (!form_ldap) {
            bad('Provide an LDAP username');
            return;
        }
        if (!form_bmo) {
            bad('Provide a Bugzilla username');
            return;
        }
        if (form_status != "PENDING"){
            if (!form_fqdn) {
                bad('Provide a FQDN');
                return;
            }
            if (!form_ipaddress) {
                bad('Provide an IP Address');
                return;
            }
        }

        var result = $.ajax({
            url: form.attr( 'action' ),
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify({status: form_status,
                                 loan_bug_id: parseInt(form_bug_id),
                                 ldap_email: form_ldap,
                                 bugzilla_email: form_bmo,
                                 fqdn: form_fqdn,
                                 ipaddress: form_ipaddress})
        }).done(function(data) {
            if (data.result) {
                good(data.result.id);
            } else {
                bad("Loan request failed in unknown way");
            }
        }).fail(function(jqhxr, err) {
            bad("error from server: " + jqhxr.statusText);
        });
    });
});

$(function() {
    var form = $('form#new-loan-request');
    var button = form.find('#submit_loan_request');
    button.click(function() {
        /* disable the button to prevent double issues */
        button.prop('disabled', true);

        var good = function(loanid) {
            reload_loans();
            alertify.success("Loan creation successful (id: " + loanid + ")");
            /* re-enable the button so we can submit a loan again */
            button.prop('disabled', false);
        };
        var bad = function(errmsg) {
            /* re-enable the button so users can try again */
            button.prop('disabled', false);
            alertify.error(errmsg);
        };

        var form_bug_id = form.find('input[name=bug_id]').val();
        var form_ldap = form.find('input[name=ldap_email]').val();
        var form_bmo = form.find('input[name=bugzilla_email]').val();
        var form_slavetype = form.find('input[name=slavetype]').val();

        var result = $.ajax({
            url: form.attr( 'action' ),
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify({loan_bug_id: parseInt(form_bug_id),
                                 ldap_email: form_ldap,
                                 bugzilla_email: form_bmo,
                                 requested_slavetype: form_slavetype})
        }).done(function(data) {
            if (data.result) {
                good(data.result.id);
            } else {
                bad("Loan request failed in unknown way");
            }
        }).fail(function(jqhxr, err) {
            bad("error from server: " + jqhxr.responseText );
        });
    });
});
