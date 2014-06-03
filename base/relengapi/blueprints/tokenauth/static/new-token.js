/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */
$(function() {
    var form = $('form#new-token');
    var button = form.find('#issue-btn');
    button.click(function() {
        /* disable the button to prevent double issues */
        button.prop('disabled', true);

        var good = function(token) {
            var token_output = form.find('div.token');
            token_output.show();
            token_output.find('.token').text(token);
            alertify.success("token issued");
        };
        var bad = function(errmsg) {
            /* re-enable the button so users can try again */
            button.prop('disabled', false);
            alertify.error(errmsg);
        };

        var checked = form.find(':checked').map(function() { return this.name }).get();
        var description = form.find('input[name=description]').val();
        if (checked.length == 0) {
            bad('Check at least one permission');
            return;
        }
        if (!description) {
            bad('Provide a description');
            return;
        }

        var result = $.ajax({
            url: '/tokenauth/tokens',
            type: 'POST',
            contentType: 'application/json; charset=utf-8',
            data: JSON.stringify({permissions: checked, description: description})
        }).done(function(data) {
            console.log(data);
            if (data.result.token) {
                good(data.result.token);
            } else {
                bad("no token received");
            }
        }).fail(function(jqhxr, err) {
            bad("error from server: " + jqhxr.statusText);
        });
    });
});
