/** @odoo-module **/

import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
import { registry } from "@web/core/registry";
import { _lt } from "@web/core/l10n/translation";

export class ProgressbarWidgetField extends ProgressBarField {
    static template = 'progressbar_widget'

    get isAnimated() {
        return this.props.record.data.hasOwnProperty('is_running') ? this.props.record.data.is_running : false;
    }
}

registry.category("fields").add("progressbar_widget", ProgressbarWidgetField);
