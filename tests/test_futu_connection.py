#!/usr/bin/env python3
"""
富途 OpenD 连接测试脚本
"""

print("🧪 富途 OpenD 连接测试")
print("=" * 60)

# 测试 1：检查富途 API 是否已安装
print("\n【测试 1】检查富途 API 安装")
try:
    from futu import OpenQuoteContext, RET_OK
    print("✅ 富途 API 已安装")
    import futu
    print(f"   版本：{futu.__version__}")
    FUTU_AVAILABLE = True
except ImportError as e:
    print(f"❌ 富途 API 未安装：{e}")
    FUTU_AVAILABLE = False

# 测试 2：检查配置文件
print("\n【测试 2】检查配置文件")
import os
config_path = os.path.join(os.path.dirname(__file__), '../config/futu_config.yaml')
if os.path.exists(config_path):
    print(f"✅ 配置文件存在：{config_path}")
else:
    print(f"❌ 配置文件不存在：{config_path}")

# 测试 3：尝试连接 OpenD
print("\n【测试 3】尝试连接富途 OpenD")
if FUTU_AVAILABLE:
    try:
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        ret, data = quote_ctx.get_market_snapshot('HK.00700')
        
        if ret == RET_OK:
            print("✅ 成功连接到富途 OpenD")
            print(f"   腾讯控股价格：{data['last_price'].iloc[0] if len(data) > 0 else 'N/A'}")
        else:
            print(f"⏳ OpenD 未启动或连接失败")
            print(f"   提示：请启动富途 OpenD GUI（默认端口 11111）")
        
        quote_ctx.close()
    except Exception as e:
        print(f"⏳ 连接异常：{str(e)}")
        print(f"   提示：请检查 OpenD 是否启动")
else:
    print("⏭️  跳过（富途 API 未安装）")

print("\n" + "=" * 60)
print("测试完成！")
