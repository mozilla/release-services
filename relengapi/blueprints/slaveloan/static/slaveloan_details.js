$( document ).ready(function() {

function reload_history() {
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
$(reload_history);

function complete_action(evt){
    evt.target.disabled = true;
    var good = function(action) {
        alertify.success("Marked action as complete");
        reload_actions();
        reload_history();
    };
    var bad = function(errmsg) {
        /* re-enable the button so users can try again */
        evt.target.disabled=false;
        alertify.error(errmsg);
    };

    var action_id = evt.target.value;
    var result = $.ajax({
        url: _get_manual_actions_base + '/' + action_id,
        type: 'PUT',
        contentType: 'application/json; charset=utf-8',
        data: JSON.stringify({complete: true})
    }).done(function(data) {
        good(data.result);
    }).fail(function(jqhxr, err) {
        bad("error from server: " + jqhxr.responseText );
    });
}

function reload_actions() {
    $('#actions_wrapper').hide();
    $('#loans-actions tbody').empty();
    $.ajax({
        url: _get_manual_actions_url,
        dataType: 'json',
        success: function(data) {
            if (data.result.length > 0) {
                $('#actions_wrapper').show();
            }
            $.each(data.result,function(i,row){
                $('<tr>').append(
                    $('<td>').text(row.timestamp_start),
                    $('<td>').text(row.msg),
                    $('<td>').append(
                        $('<button type="button" value="' + row.id + '">COMPLETE</button>.').click(
                            complete_action
                        )
                    )
                ).appendTo('#loans-actions tbody');
            });
        }
    });
}
$(reload_actions);

$('#complete_loan').click(
  function() {
    // XXX When has any automatic parts, make a confirmation
    $.ajax({
        type: 'DELETE',
        url: _complete_loan_url,
        dataType: 'json',
        success: function(data) {
            alertify.success("Successfully marked loan as Complete (Relinquished)");
            reload_history();
        }
    })
  }
);

});
