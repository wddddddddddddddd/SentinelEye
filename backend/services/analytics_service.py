from datetime import datetime, timedelta


def get_current_week_range(date_str=None, date_format="%Y.%m.%d", output_format="%Y.%m.%d"):
    """
    获取指定日期所在周的日期范围

    参数:
        date_str: 指定日期字符串，如果为None则使用当前日期
        date_format: 输入日期的格式
        output_format: 输出日期的格式

    返回:
        字符串: "起始日期~结束日期"
    """
    # 获取目标日期
    if date_str:
        target_date = datetime.strptime(date_str, date_format)
    else:
        target_date = datetime.now()

    # 计算本周的周一（周一是第一天）
    week_start = target_date - timedelta(days=target_date.weekday())
    # 计算本周的周日
    week_end = week_start + timedelta(days=6)

    # 格式化输出
    start_str = week_start.strftime(output_format)
    end_str = week_end.strftime(output_format)

    week_datetime_info = {
        'week_start_date': start_str,
        'week_end_date': end_str
    }
    return week_datetime_info


# 使用示例
print(get_current_week_range())  # 默认使用今天
print(get_current_week_range("2025.12.14"))  # 指定日期