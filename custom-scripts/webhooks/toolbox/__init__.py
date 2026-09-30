import logging
import os
import time

log = logging.getLogger(__name__)

# Main Webhook Handler Entry Point
def main(trans, webhook, params):
    """
    Handles HTTP GET requests sent to:
    /api/webhooks/toolbox/data

    Parameters:
        trans (GalaxyWebTransaction): Current Galaxy transaction object containing application context.
        webhook (Webhook): Webhook object instance.
        params (dict): Request parameters (e.g., {'action': 'status'} or {'action': 'reload'}).
    """
    app = trans.app
    action = params.get("action", "reload")
    target_xml = 'bootstrap_tools_conf.xml'

    # Check reload status during background execution
    if action == "status":
        in_progress = getattr(app, "_webhook_reload_in_progress", False)
        if not in_progress:
            return {"reloading": False}

        start_count = getattr(app, "_webhook_reload_start_count", 0)
        current_count = getattr(app.toolbox, "_reload_count", 0)
        elapsed = time.time() - getattr(app, "_webhook_reload_trigger_time", 0)

        # Reload is complete once toolbox count increments AND 10-second search-indexing window completes
        if current_count > start_count and elapsed >= 10:
            app._webhook_reload_in_progress = False
            return {"reloading": False}

        return {"reloading": True}

    # Resolve bootstrap configuration file path
    raw_bootstrap_path = os.path.abspath(
        os.path.join(app.config.root, 'bootstrap/config/bootstrap_tools_conf.xml')
    )

    # Append configuration file to app config
    tool_configs = app.config.tool_config_file
    if isinstance(tool_configs, str):
        tool_configs = [c.strip() for c in tool_configs.split(',')]
        app.config.tool_config_file = tool_configs

    if not any(target_xml in str(cfg) for cfg in tool_configs):
        tool_configs.append(raw_bootstrap_path)
        log.info(f"Appended {raw_bootstrap_path} to app.config.tool_config_file")

    # Append configuration file directly to active toolbox instance
    if hasattr(app.toolbox, "config_filenames"):
        tb_configs = app.toolbox.config_filenames
        if isinstance(tb_configs, list):
            if not any(target_xml in str(cfg) for cfg in tb_configs):
                tb_configs.append(raw_bootstrap_path)
        elif isinstance(tb_configs, tuple):
            if not any(target_xml in str(cfg) for cfg in tb_configs):
                app.toolbox.config_filenames = tb_configs + (raw_bootstrap_path,)
        log.info(f"Appended {raw_bootstrap_path} to app.toolbox.config_filenames")

    # Track lifecycle state and dispatch background reload task
    app._webhook_reload_start_count = getattr(app.toolbox, "_reload_count", 0)
    app._webhook_reload_trigger_time = time.time()
    app._webhook_reload_in_progress = True

    # Send background control task across processes/workers to execute toolbox reload
    app.queue_worker.send_control_task("reload_toolbox")

    return {
        "status": "success",
        "message": "Toolbox reload initiated."
    }
