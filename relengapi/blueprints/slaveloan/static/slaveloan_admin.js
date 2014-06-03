function reload_loans() {
    $('#loans-table tbody').empty();
    $.ajax({
        url: _get_loans_url,
        dataType: 'json',
        success: function(data) {
            $.each(data.result,function(i,row){
                var $tr = $('<tr>').append(
                    $('<td>').text(row.status),
                    $('<td>').text(row.human.ldap),
                    $('<td>').text(row.human.bugzilla),
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
            token_output.find('.token').text(token);
            alertify.success("Loan entry created");
        };
        var bad = function(errmsg) {
            /* re-enable the button so users can try again */
            button.prop('disabled', false);
            alertify.error(errmsg);
        };

        var form_status = form.find('select[name=status]').val();
        var form_ldap = form.find('input[name=LDAP]').val();
        var form_bmo = form.find('input[name=bugzilla]').val();
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
        if (!form_fqdn) {
            bad('Provide a FQDN');
            return;
        }
        if (!form_ipaddr) {
            bad('Provide an IP Address');
            return;
        }

        var result = $.ajax({
            url: form.attr( 'action' ),
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify({status: form_status,
                                 LDAP: form_ldap,
                                 bugzilla: form_bmo,
                                 fqdn: form_fqdn,
                                 ipaddr: form_ipaddr})
        }).done(function(data) {
            console.log(data);
            if (data.result.token) {
                good(data.result.loan);
            } else {
                bad("Loan request failed in unknown way");
            }
        }).fail(function(jqhxr, err) {
            bad("error from server: " + jqhxr.statusText);
        });
    });
});