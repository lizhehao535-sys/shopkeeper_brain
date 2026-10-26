from pathlib import Path

import json

from knowledge.processor.import_process.base import BaseNode, setup_logging
from knowledge.processor.import_process.exceptions import ValidationError
from knowledge.processor.import_process.state import ImportGraphState


class EntryNode(BaseNode):
    """
       入口节点

       根据输入文件的扩展名设置相应的处理标志，
       决定后续流程走 PDF 转换分支还是直接处理 MD 分支。
       """

    name = "entry_node"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        处理文件类型的检测


        Args:
            state: ImportGraphState 该节点处理之前的节点状态

        Returns:
            ImportGraphState：该节点处理之后的节点状态
        """
        self.log_step("step1","获取文件")
        # 1. 获取导入的文件路径以及文件所在的目录
        file_dir = state.get('file_dir')
        import_file_path = state.get('import_file_path')
        self.log_step("step2", "获取文件是否存在")
        # 2. 简单校验一下 文件路径以及所在目录
        if  not import_file_path:
            raise ValidationError("文件目录或者文件不存在", self.name)

        # 3. 使用标准的Path对象操作文件逻辑
        path = Path(import_file_path)
        if not path.exists():
            raise ValidationError(f"文件不存在：{import_file_path}",self.name)

        # 4. 获取上传文件的后缀
        suffix = path.suffix.lower()

        # 5. 判断文件的后缀
        self.log_step("step3", "获取文件类型")
        if suffix == '.pdf':
            state['is_pdf_read_enabled'] = True
            state['pdf_path'] = import_file_path
        elif suffix == '.md':
            state['is_md_read_enabled'] = True
            state['md_path'] = import_file_path
        else:
            self.logger.debug(f"文件类型{suffix}不支持")
            raise ValidationError(f"文件类型{suffix}不支持")

        # 6. 获取文件的标题名
        file_title = path.stem
        state['file_title'] = file_title

        # 7. 返回state
        return state


# ================================================================== #
#                        测试                                        #
# ================================================================== #



if __name__ == '__main__':
    setup_logging()

    # 方式：直接实例该节点对象，调用 process 方法
    # 1. 构建该节点需要的 state
    import_file_path = r"D:\doc\万用表RS-12的使用.pdf"
    file_dir = r"D:\temp_dir"
    state = {
        "is_pdf_read_enable": True,
        "is_md_read_enable": False,
        "import_file_path": import_file_path,
        "file_dir": file_dir
    }

    # 2. 实例 EntryNode 节点
    entry = EntryNode()

    # 3. 调用 process 方法
    processed_entry = entry(state)

    # 序列化打印
    print(json.dumps(processed_entry, ensure_ascii=False, indent=4))







