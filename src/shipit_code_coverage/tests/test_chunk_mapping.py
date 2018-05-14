# -*- coding: utf-8 -*-
import os
import sqlite3
import tarfile

import pytest
import responses

from shipit_code_coverage import chunk_mapping

LINUX_XPCSHELL1 = set(['browser/extensions/formautofill/test/unit/heuristics/third_party/test_Staples.js', 'browser/components/syncedtabs/test/xpcshell/test_EventEmitter.js', 'devtools/server/tests/unit/test_frameclient-01.js', 'browser/extensions/formautofill/test/unit/test_isFieldEligibleForAutofill.js', 'browser/components/sessionstore/test/unit/test_migration_lz4compression.js', 'browser/modules/test/unit/test_AttributionCode.js', 'chrome/test/unit/test_bug564667.js', 'devtools/server/tests/unit/test_breakpoint-18.js', 'browser/components/places/tests/unit/test_browserGlue_distribution.js', 'devtools/client/shared/test/unit/test_cubicBezier.js', 'devtools/server/tests/unit/test_animation_type.js', 'xpcshell-remote.ini:browser/components/extensions/test/xpcshell/test_ext_browsingData_cookies_cache.js', 'xpcshell.ini:browser/components/extensions/test/xpcshell/test_ext_url_overrides_newtab_update.js', 'devtools/server/tests/unit/test_eval-02.js', 'devtools/client/inspector/animation-old/test/unit/test_timeScale_dimensions.js', 'devtools/server/tests/unit/test_objectgrips-01.js', 'devtools/server/tests/unit/test_breakpoint-20.js', 'browser/components/syncedtabs/test/xpcshell/test_SyncedTabsDeckStore.js', 'browser/extensions/formautofill/test/unit/heuristics/third_party/test_BestBuy.js', 'devtools/server/tests/unit/test_frameactor-02.js', 'xpcshell-remote.ini:browser/components/extensions/test/xpcshell/test_ext_browsingData_downloads.js', 'browser/components/migration/tests/unit/test_MigrationUtils_timedRetry.js', 'devtools/server/tests/unit/test_frameactor-05.js', 'devtools/server/tests/unit/test_sourcemaps-07.js', 'devtools/client/performance/test/unit/test_perf-utils-allocations-to-samples.js', 'browser/components/migration/tests/unit/test_IE7_passwords.js', 'devtools/server/tests/unit/test_objectgrips-10.js', 'browser/extensions/formautofill/test/unit/test_storage_tombstones.js', 'browser/modules/test/unit/test_Sanitizer_interrupted.js', 'devtools/client/shared/test/unit/test_parseDeclarations.js', 'devtools/server/tests/unit/test_listsources-04.js', 'devtools/client/performance/test/unit/test_tree-model-02.js', 'xpcshell.ini:browser/components/extensions/test/xpcshell/test_ext_geckoProfiler_schema.js', 'xpcshell-remote.ini:browser/components/extensions/test/xpcshell/test_ext_chrome_settings_overrides_update.js', 'devtools/server/tests/unit/test_promises_actor_list_promises.js', 'devtools/server/tests/unit/test_breakpoint-15.js', 'browser/components/migration/tests/unit/test_Edge_db_migration.js', 'devtools/server/tests/unit/test_breakpoint-07.js', 'devtools/client/performance/test/unit/test_tree-model-07.js', 'devtools/server/tests/unit/test_MemoryActor_saveHeapSnapshot_01.js', 'devtools/server/tests/unit/test_breakpoint-08.js', 'devtools/client/memory/test/unit/test_action-filter-03.js', 'devtools/client/inspector/animation-old/test/unit/test_timeScale.js', 'caps/tests/unit/test_origin.js', 'devtools/server/tests/unit/test_getTextAtLineColumn.js', 'devtools/client/memory/test/unit/test_tree-map-02.js', 'browser/extensions/formautofill/test/unit/test_migrateRecords.js', 'xpcshell.ini:browser/components/extensions/test/xpcshell/test_ext_url_overrides_newtab.js', 'devtools/client/memory/test/unit/test_action-filter-02.js', 'devtools/server/tests/unit/test_sourcemaps-10.js', 'devtools/client/memory/test/unit/test_pop_view_01.js', 'devtools/server/tests/unit/test_addon_reload.js', 'xpcshell.ini:browser/components/extensions/test/xpcshell/test_ext_pageAction_shutdown.js', 'devtools/client/performance/test/unit/test_tree-model-09.js', 'devtools/client/shared/test/unit/test_VariablesView_filtering-without-controller.js', 'devtools/server/tests/unit/test_breakpoint-10.js', 'browser/extensions/formautofill/test/unit/test_getInfo.js', 'devtools/client/memory/test/unit/test_action_diffing_05.js', 'browser/components/migration/tests/unit/test_360se_bookmarks.js', 'browser/extensions/formautofill/test/unit/test_getCategoriesFromFieldNames.js', 'devtools/server/tests/unit/test_eval-04.js', 'devtools/client/memory/test/unit/test_dominator_trees_09.js', 'browser/components/migration/tests/unit/test_automigration.js', 'devtools/server/tests/unit/test_conditional_breakpoint-02.js', 'devtools/server/tests/unit/test_dbgactor.js', 'devtools/client/inspector/grids/test/unit/test_compare_fragments_geometry.js', 'devtools/client/responsive.html/test/unit/test_add_viewport.js', 'devtools/client/performance/test/unit/test_tree-model-13.js', 'browser/components/migration/tests/unit/test_IE_bookmarks.js', 'devtools/client/shared/test/unit/test_source-utils.js', 'devtools/server/tests/unit/test_breakpoint-05.js', 'devtools/client/memory/test/unit/test_action_diffing_02.js', 'devtools/client/shared/test/unit/test_cssColor-03.js', 'devtools/client/responsive.html/test/unit/test_add_device.js', 'browser/extensions/formautofill/test/unit/test_creditCardRecords.js', 'devtools/client/memory/test/unit/test_dominator_trees_02.js', 'devtools/server/tests/unit/test_nesting-01.js', 'devtools/server/tests/unit/test_register_actor.js', 'browser/extensions/onboarding/test/unit/test-onboarding-tour-type.js', 'devtools/server/tests/unit/test_breakpoint-22.js', 'browser/extensions/formautofill/test/unit/test_storage_syncfields.js', 'browser/extensions/formautofill/test/unit/heuristics/third_party/test_CDW.js', 'devtools/server/tests/unit/test_new_source-01.js', 'xpcshell.ini:browser/components/extensions/test/xpcshell/test_ext_browsingData.js', 'devtools/server/tests/unit/test_protocol_formtype.js', 'devtools/client/shared/vendor/stringvalidator/tests/unit/test_validators.js', 'devtools/client/netmonitor/test/unit/test_mdn-utils.js', 'browser/extensions/formautofill/test/unit/test_extractLabelStrings.js', 'xpcshell-remote.ini:browser/components/extensions/test/xpcshell/test_ext_history.js', 'devtools/server/tests/unit/test_threadlifetime-03.js', 'devtools/client/memory/test/unit/test_action-export-snapshot.js', 'browser/components/migration/tests/unit/test_Chrome_cookies.js'])  # noqa
WINDOWS_MOCHITEST1 = set(['docshell/test/test_bug694612.html', 'caps/tests/mochitest/test_bug1367586.html', 'docshell/test/iframesandbox/test_child_navigation_by_location.html', 'docshell/test/test_bug1045096.html', 'docshell/test/navigation/test_sibling-matching-parent.html', 'docshell/test/iframesandbox/test_our_auxiliary_navigation_by_location.html', 'docshell/test/test_anchor_scroll_after_document_open.html', 'dom/browser-element/mochitest/test_browserElement_oop_getWebManifest.html', 'docshell/test/navigation/test_bug430723.html', 'browser/components/payments/test/mochitest/test_shipping_option_picker.html', 'docshell/test/test_bug1186774.html', 'dom/browser-element/mochitest/test_browserElement_oop_Opensearch.html', 'docshell/test/test_bug529119-1.html', 'browser/components/originattributes/test/mochitest/test_permissions_api.html', 'dom/animation/test/css-animations/test_animation-cancel.html', 'browser/components/payments/test/mochitest/test_currency_amount.html', 'dom/browser-element/mochitest/test_browserElement_oop_Alert.html', 'dom/browser-element/mochitest/test_browserElement_inproc_BrowserWindowResize.html', 'dom/browser-element/mochitest/test_browserElement_inproc_Alert.html', 'dom/browser-element/mochitest/test_browserElement_inproc_Auth.html', 'dom/browser-element/mochitest/test_browserElement_inproc_dataBlock.html', 'dom/animation/test/css-animations/test_keyframeeffect-getkeyframes.html', 'dom/animation/test/css-transitions/test_element-get-animations.html', 'browser/components/payments/test/mochitest/test_rich_select.html', 'dom/browser-element/mochitest/test_browserElement_inproc_PromptCheck.html', 'dom/abort/tests/test_abort_controller.html', 'docshell/test/navigation/test_bug386782.html', 'browser/components/feeds/test/test_bug494328.html', 'docshell/test/navigation/test_bug344861.html', 'dom/browser-element/mochitest/test_browserElement_inproc_FrameWrongURI.html', 'docshell/test/navigation/test_bug278916.html', 'docshell/test/test_bug728939.html', 'dom/browser-element/mochitest/test_browserElement_inproc_PromptConfirm.html', 'docshell/test/test_pushState_after_document_open.html', 'dom/browser-element/mochitest/test_browserElement_oop_OpenMixedProcess.html', 'dom/browser-element/mochitest/test_browserElement_oop_BadScreenshot.html', 'dom/animation/test/css-transitions/test_event-dispatch.html', 'docshell/test/navigation/test_contentpolicy_block_window.html', 'dom/browser-element/mochitest/test_browserElement_inproc_RemoveBrowserElement.html', 'dom/animation/test/css-animations/test_animation-playstate.html', 'dom/browser-element/mochitest/test_browserElement_inproc_XFrameOptionsAllowFrom.html', 'browser/components/payments/test/mochitest/test_payment_method_picker.html', 'dom/animation/test/css-animations/test_pseudoElement-get-animations.html', 'docshell/test/iframesandbox/test_other_auxiliary_navigation_by_location.html', 'widget/tests/test_picker_no_crash.html', 'docshell/test/test_bug675587.html', 'browser/extensions/formautofill/test/mochitest/test_address_level_1_submission.html', 'docshell/test/test_bug551225.html', 'docshell/test/test_bug387979.html', 'dom/animation/test/css-animations/test_event-order.html', 'dom/animation/test/css-transitions/test_animation-currenttime.html', 'browser/extensions/formautofill/test/mochitest/test_on_address_submission.html', 'docshell/test/navigation/test_bug270414.html', 'dom/animation/test/css-transitions/test_pseudoElement-get-animations.html', 'dom/animation/test/css-animations/test_animations-dynamic-changes.html', 'dom/animation/test/css-animations/test_animation-currenttime.html', 'dom/browser-element/mochitest/test_browserElement_oop_Iconchange.html', 'docshell/test/navigation/test_grandchild.html', 'dom/animation/test/css-transitions/test_animation-cancel.html', 'caps/tests/mochitest/test_bug423375.html', 'browser/components/resistfingerprinting/test/mochitest/test_speech_synthesis.html', 'browser/components/resistfingerprinting/test/mochitest/test_keyboard_event.html', 'dom/browser-element/mochitest/test_browserElement_oop_OpenWindowEmpty.html', 'docshell/test/navigation/test_triggeringprincipal_frame_nav.html', 'dom/animation/test/css-animations/test_animation-starttime.html', 'browser/extensions/formautofill/test/mochitest/test_form_changes.html', 'dom/browser-element/mochitest/test_browserElement_inproc_XFrameOptions.html', 'devtools/shared/heapsnapshot/tests/mochitest/test_saveHeapSnapshot_e10s_01.html', 'dom/animation/test/css-transitions/test_setting-effect.html', 'dom/browser-element/mochitest/test_browserElement_oop_Manifestchange.html', 'dom/browser-element/mochitest/test_browserElement_oop_ForwardName.html', 'docshell/test/iframesandbox/test_top_navigation_by_location.html', 'docshell/test/navigation/test_bug1364364.html', 'dom/animation/test/css-transitions/test_animation-computed-timing.html', 'docshell/test/test_bug580069.html', 'docshell/test/test_bug123696.html', 'docshell/test/navigation/test_not-opener.html', 'docshell/test/test_bug475636.html', 'dom/browser-element/mochitest/test_browserElement_oop_XFrameOptionsSameOrigin.html'])  # noqa


@pytest.fixture
def fake_artifacts_handler(grcov_artifact, jsvm_artifact, grcov_existing_file_artifact, grcov_uncovered_function_artifact):
    class FakeArtifactsHandler(object):
        def __init__(self):
            pass

        def get_chunks(self):
            return ['chunk1', 'chunk2']

        def get(self, platform=None, suite=None, chunk=None):
            if platform == 'linux' and chunk == 'chunk1':
                return [grcov_artifact]  # js/src/jit/BitSet.cpp
            elif platform == 'linux' and chunk == 'chunk2':
                return [jsvm_artifact]  # toolkit/components/osfile/osfile.jsm
            elif platform == 'windows' and chunk == 'chunk1':
                return [grcov_existing_file_artifact]  # shipit_code_coverage/cli.py
            elif platform == 'windows' and chunk == 'chunk2':
                return [grcov_uncovered_function_artifact]  # js/src/jit/JIT.cpp

    return FakeArtifactsHandler()


def assert_file_to_chunk(c, path, platform, chunk):
    c.execute('SELECT platform, chunk FROM file_to_chunk WHERE path=?', (path,))
    results = c.fetchall()
    assert len(results) == 1
    assert results[0][0] == platform
    assert results[0][1] == chunk


@responses.activate
def test_zero_coverage(tmpdir, fake_artifacts_handler, fake_hg_repo, ACTIVEDATA_CHUNK_TO_TESTS):
    tmp_path = tmpdir.strpath

    chunk_mapping.generate(
        fake_hg_repo,
        '632bb768b1dd4b96a196412e8f7b669ca09d6d91',
        fake_artifacts_handler,
        out_dir=tmp_path,
    )

    with tarfile.open(os.path.join(tmp_path, 'chunk_mapping.tar.xz')) as t:
        t.extract('chunk_mapping.sqlite', tmp_path)

    with sqlite3.connect(os.path.join(tmp_path, 'chunk_mapping.sqlite')) as conn:
        c = conn.cursor()

        assert_file_to_chunk(c, 'js/src/jit/BitSet.cpp', 'linux', 'chunk1')
        assert_file_to_chunk(c, 'toolkit/components/osfile/osfile.jsm', 'linux', 'chunk2')
        assert_file_to_chunk(c, 'shipit_code_coverage/cli.py', 'windows', 'chunk1')
        assert_file_to_chunk(c, 'js/src/jit/JIT.cpp', 'windows', 'chunk2')

        c.execute('SELECT path FROM chunk_to_test WHERE platform=? AND chunk=?', ('linux', 'xpcshell-1'))
        assert set([e[0] for e in c.fetchall()]) == LINUX_XPCSHELL1

        c.execute('SELECT path FROM chunk_to_test WHERE platform=? AND chunk=?', ('windows', 'mochitest-1'))
        assert set([e[0] for e in c.fetchall()]) == WINDOWS_MOCHITEST1
