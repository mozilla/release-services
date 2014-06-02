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
