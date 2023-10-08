/** @odoo-module **/

import { ProgressBarField } from "@web/views/fields/progress_bar/progress_bar_field";
import { formatFloatTime } from "@web/views/fields/formatters";
import { registry } from "@web/core/registry";
import { _lt } from "@web/core/l10n/translation";

export class ProgressbarWidgetField extends ProgressBarField {
    static template = 'progressbar_widget'

    setup() {
        super.setup();
        this.progress_bar_data = [];
        if (this.props.value && this.props.value.includes(',')) {
            let items = this.props.value.split(',');
            for (let index = 0; index < items.length; index++) {
                let item = items[index];
                let [progress, duration] = item.split(';');
                this.progress_bar_data.push({ progress: progress, duration: formatFloatTime(duration), index: index });
            }
        } else if (this.props.value) {
            let [progress, duration] = this.props.value.split(';');
            this.progress_bar_data.push({ progress: progress, duration: formatFloatTime(duration), index: 0 });
        }
    }

    get getProgressBar() {
        return this.progress_bar_data;
    }

//    get isAnimated() {
//        return this.props.record.data.hasOwnProperty('is_running') ? this.props.record.data.is_running : false;
//    }
}

registry.category("fields").add("progressbar_widget", ProgressbarWidgetField);
