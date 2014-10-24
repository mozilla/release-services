function reload_loans() {
    $('#loans-table tbody').empty();
    $.ajax({
        url: _get_loans_url,
        dataType: 'json',
        success: function(data) {
            $.each(data.result,function(i,row){
                $('<tr>').append(
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
                    $('<td>').text(row.human.bugzilla_email),
                    $('<td>').text(row.machine.fqdn),
                    $('<td>').text(row.machine.ipaddr)
                ).appendTo('#loans-table tbody');
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

        var good = function(loan) {
            reload_loans();
            alertify.success("Loan entry created");
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
        var form_ldap = form.find('input[name=ldap_email]').val();
        var form_bmo = form.find('input[name=bugzilla_email]').val();
        var form_fqdn = form.find('input[name=fqdn]').val();
        var form_ipaddr = form.find('input[name=ipaddr]').val();
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
            if (!form_ipaddr) {
                bad('Provide an IP Address');
                return;
            }
        }

        var result = $.ajax({
            url: form.attr( 'action' ),
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify({status: form_status,
                                 ldap_email: form_ldap,
                                 bugzilla_email: form_bmo,
                                 fqdn: form_fqdn,
                                 ipaddr: form_ipaddr})
        }).done(function(data) {
            console.log(data);
            if (data.result.loan) {
                good(data.result.loan);
            } else {
                bad("Loan request failed in unknown way");
            }
        }).fail(function(jqhxr, err) {
            bad("error from server: " + jqhxr.statusText);
        });
    });
});
