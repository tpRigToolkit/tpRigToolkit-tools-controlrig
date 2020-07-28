if __name__ == '__main__':
    import tpDcc
    import tpRigToolkit.loader

    tpRigToolkit.loader.init()
    tpDcc.ToolsMgr().launch_tool_by_id('tpRigToolkit-tools-controlrig')
