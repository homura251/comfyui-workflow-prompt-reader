__author__ = "receyuki"
__filename__ = "cli.py"
__copyright__ = "Copyright 2024"
__email__ = "receyuki@gmail.com"

import json
from pathlib import Path

import click
from .image_data_reader import ImageDataReader
from .constants import SUPPORTED_FORMATS
from .logger import Logger


@click.command()
# Feature mode
@click.option(
    "-r", "--read", "operation", flag_value="read", help="读取模式", default=True
)
@click.option("-w", "--write", "operation", flag_value="write", help="写入模式")
@click.option("-c", "--clear", "operation", flag_value="clear", help="清除模式")
# Option
@click.option("-i", "--input-path", type=str, help="输入路径", required=True)
@click.option("-o", "--output-path", type=str, help="输出路径")
@click.option(
    "-f",
    "--format-type",
    default="TXT",
    type=click.Choice(["TXT", "JSON"], case_sensitive=False),
)
@click.option("-m", "--metadata", type=str, help="元数据文件")
@click.option("-p", "--positive", type=str, help="正向提示词")
@click.option("-n", "--negative", type=str, help="反向提示词")
@click.option("-s", "--setting", type=str, help="参数")
@click.option(
    "-l",
    "--log-level",
    default="WARN",
    type=click.Choice(["DEBUG", "INFO", "WARN", "ERROR"], case_sensitive=False),
)
def cli(
    operation,
    input_path,
    output_path,
    metadata,
    positive,
    negative,
    setting,
    format_type,
    log_level,
):

    logger = Logger("SD_Prompt_Reader.Cli")
    Logger.configure_global_logger(log_level)

    # Ensure the input path exists
    source = Path(input_path)
    logger.debug(f"Input: {source}")
    if not source.exists():
        logger.error("输入路径不存在")
        raise click.UsageError("指定的输入路径不存在。")
    elif source.is_file():
        logger.debug("输入为文件")
        file_list = [input_path]
    else:
        logger.debug("输入为文件夹")
        file_list = [
            file
            for file in source.glob("*")
            if file.is_file() and file.suffix in SUPPORTED_FORMATS
        ]
        logger.debug(f"检测到文件数：{len(file_list)}")

    match operation:
        case "read":
            logger.debug("读取模式")
            success_count = 0
            read_list = {}
            failure_list = {}
            for file in file_list:
                logger.debug(f"读取文件：{file}")
                with open(file, "rb") as f:
                    image_data = ImageDataReader(f)
                    if image_data.status.name == "READ_SUCCESS":
                        logger.debug("读取成功")
                        success_count += 1
                        if source.is_file():
                            click.echo(image_data.raw)
                        read_list[file] = image_data
                    else:
                        logger.warning(
                            f"读取失败：{file}（原因：{image_data.status.name}）"
                        )
                        failure_list[file] = image_data.status.name
            if source.is_dir():
                logger.info(f"读取文件总数：{len(file_list)}")
                logger.info(f"成功：{success_count}")
                if failure_list:
                    logger.info("失败列表：")
                    for file, status in failure_list.items():
                        logger.info(f"{file}: {status}")

            if output_path:
                target = Path(output_path)
                logger.debug(f"输出：{target}")
                for file, image_data in read_list.items():
                    logger.debug(f"导出文件：{file}")
                    file_path = Path(file)
                    if target.is_dir():
                        logger.debug("输出目录已存在")
                        folder = target
                        stem = file_path.stem
                    elif target.is_file():
                        if source.is_dir():
                            logger.error("输出路径为文件而不是目录")
                            raise click.UsageError(
                                "当输入路径为目录时，输出路径必须为目录，不能是文件。"
                            )
                        logger.debug("输出文件已存在，将覆盖旧文件")
                        folder = target.parent
                        stem = target.stem
                        if not format_type:
                            format_type = target.suffix.strip(".")
                    else:
                        if target.suffix:
                            if source.is_dir():
                                logger.error("输出路径为文件而不是目录")
                                raise click.UsageError(
                                    "当输入路径为目录时，输出路径必须为目录，不能是文件。"
                                )
                            logger.debug("输出文件不存在")
                            logger.debug("将创建新文件")
                            folder = target.parent
                            stem = target.stem
                            if not format_type:
                                format_type = target.suffix.strip(".")
                        else:
                            logger.debug("输出目录不存在")
                            logger.debug("将创建新目录")
                            folder = target
                            stem = file_path.stem
                        folder.mkdir(parents=True, exist_ok=True)
                    target_file_name = folder / stem
                    try:
                        match format_type:
                            case "TXT":
                                logger.debug("输出格式：TXT")
                                with open(
                                    target_file_name.with_suffix(".txt"),
                                    "w",
                                    encoding="utf-8",
                                ) as f:
                                    f.write(image_data.raw)
                                    logger.debug("导出成功")
                            case "JSON":
                                logger.debug("输出格式：JSON")
                                with open(
                                    target_file_name.with_suffix(".json"),
                                    "w",
                                    encoding="utf-8",
                                ) as f:
                                    parameter = {
                                        "positive": image_data.positive,
                                        "negative": image_data.negative,
                                        "setting": image_data.setting,
                                    }
                                    parameter.update(image_data.parameter)
                                    json.dump(parameter, f, indent=4)
                                    logger.debug("导出成功")
                            case _:
                                logger.error(
                                    f"不支持的输出格式：{format_type}（仅支持 TXT/JSON）"
                                )
                    except IOError as e:
                        logger.error(f"保存失败：{e}")

        case "write" | "clear":
            if operation == "write":
                logger.debug("写入模式")
                if source.is_dir():
                    logger.error("输入为目录而不是文件")
                    raise click.UsageError(
                        "写入模式下，输入路径必须是文件，不能是目录。"
                    )
                if metadata:
                    logger.debug("已指定元数据文件")
                    metadata_path = Path(metadata)
                    with open(metadata_path, "rb") as f:
                        if metadata_path.suffix.lower() == ".txt":
                            data = f.read()
                        elif metadata_path.suffix.lower() == ".json":
                            data_dict = json.load(f)
                            data = ImageDataReader.construct_data(
                                data_dict.get("positive"),
                                data_dict.get("negative"),
                                data_dict.get("setting"),
                            )
                        else:
                            data = ""
                        click.echo(data)
                elif positive or negative or setting:
                    logger.debug("已指定元数据文本")
                    data = ImageDataReader.construct_data(positive, negative, setting)
                    click.echo(data)
            if operation == "clear":
                logger.debug("清除模式")
            success_count = 0
            if output_path:
                target = Path(output_path)
                logger.debug(f"输出：{target}")
                for file in file_list:
                    logger.debug(f"处理文件：{file}")
                    file_path = Path(file)
                    if target.is_dir():
                        logger.debug("输出目录已存在")
                        folder = target
                        stem = file_path.stem
                    elif target.is_file():
                        if source.is_dir():
                            logger.error("输出路径为文件而不是目录")
                            raise click.UsageError(
                                "当输入路径为目录时，输出路径必须为目录，不能是文件。"
                            )
                        logger.debug("输出文件已存在，将覆盖旧文件")
                        folder = target.parent
                        stem = target.stem
                    else:
                        if target.suffix:
                            if source.is_dir():
                                logger.error("输出路径为文件而不是目录")
                                raise click.UsageError(
                                    "当输入路径为目录时，输出路径必须为目录，不能是文件。"
                                )
                            logger.debug("输出文件不存在")
                            logger.debug("将创建新文件")
                            folder = target.parent
                            stem = target.stem
                        else:
                            logger.debug("输出目录不存在")
                            logger.debug("将创建新目录")
                            folder = target
                            stem = file_path.stem
                        folder.mkdir(parents=True, exist_ok=True)
                    target_file_name = folder / stem
                    try:
                        ImageDataReader.save_image(
                            file,
                            target_file_name.with_suffix(file_path.suffix),
                            file_path.suffix.lstrip(".").upper(),
                            None if operation == "clear" else data,
                        )
                    except IOError as e:
                        logger.error(f"保存失败：{e}")
                    else:
                        logger.debug("输出成功")
                        success_count += 1
            else:
                logger.debug("未指定输出路径，输出到原始目录")
                for file in file_list:
                    file_path = Path(file)
                    folder = file_path.parent
                    stem = (
                        f"{file_path.stem}_data_removed{file_path.suffix}"
                        if operation == "clear"
                        else f"{file_path.stem}_edited{file_path.suffix}"
                    )
                    target_file_name = folder / stem
                    try:
                        ImageDataReader.save_image(
                            file,
                            target_file_name,
                            file_path.suffix.lstrip(".").upper(),
                            None if operation == "clear" else data,
                        )
                    except IOError as e:
                        logger.error(f"保存失败：{e}")
                    else:
                        logger.debug("输出成功")
                        success_count += 1

            if len(file_list) > 1:
                logger.info(f"处理文件总数：{len(file_list)}")
                logger.info(f"成功：{success_count}")


if __name__ == "__main__":
    cli()
