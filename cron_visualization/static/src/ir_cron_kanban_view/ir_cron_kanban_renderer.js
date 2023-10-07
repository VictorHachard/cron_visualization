/** @odoo-module **/

import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";

const { onWillStart } = owl;
var rpc = require('web.rpc');

export class IrCronKanbanRenderer extends KanbanRenderer {

}

IrCronKanbanRenderer.template = "cron_visualization.IrCronKanbanRenderer";
