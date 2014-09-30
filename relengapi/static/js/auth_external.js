/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

$(function() {
    var authAjax = function(url, action) {
        return $.ajax({
            url: url + '?ajax=1',
            success: function(res, status, xhr) {
                return location.reload(true);
            },
            error: function(res, status, xhr) {
                alertify.error(action + " failure: " + status);
            }
        });
    }
    $('button#login').click(function() { authAjax('/userauth/login', 'login'); });
    $('button#logout').click(function() { authAjax('/userauth/logout', 'logout'); });
});
