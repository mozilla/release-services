function reload_loans() {
    $('#loans-history tbody').empty();
    $.ajax({
        url: _get_history_url,
        dataType: 'json',
        success: function(data) {
            $.each(data.result,function(i,row){
                $('<tr>').append(
                    $('<td>').text(row.timestamp),
                    $('<td>').text(row.msg)
                ).appendTo('#loans-history tbody');
            });
        }
    });
}
$(reload_loans);
