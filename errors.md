# 首轮典型错误分析

错误条目共 30 条，全部来自被测作答方（mock 助手，基于固定桩）实际输出与标注的不匹配记录；原因分类由不匹配内容推导，无预设标签。

## 1. KB-SOP-025

- 问题/路由：投影仪坏了怎么办？
- 期望：{"expected_doc_ids": ["SOP-REPAIR"], "expected_points": ["在小程序报修入口提交", "IT 支持 30 分钟内响应"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [],
    "cited_doc_ids": [],
    "first_token_ms": 0.091,
    "refused": true,
    "total_ms": 0.091
  }
  ```
- 判定：answerable item was refused；missing expected points: ['在小程序报修入口提交', 'IT 支持 30 分钟内响应']
- 原因分类：point_miss
- 修复类别：answer-composition

## 2. KB-SOP-030

- 问题/路由：报修单填错了怎么改？
- 期望：{"expected_doc_ids": ["SOP-REPAIR"], "expected_points": ["处理前可在小程序撤回重报", "已派单的工单联系物业修改"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "报修入口：在小程序报修入口提交工单，IT 或物业 30 分钟内响应",
      "验收关闭：报修完成后须在小程序确认验收，未确认 24 小时后自动关闭"
    ],
    "cited_doc_ids": [
      "SOP-REPAIR"
    ],
    "first_token_ms": 0.13,
    "refused": false,
    "total_ms": 0.131
  }
  ```
- 判定：missing expected points: ['处理前可在小程序撤回重报', '已派单的工单联系物业修改']
- 原因分类：point_miss
- 修复类别：answer-composition

## 3. KB-SPC-001

- 问题/路由：会员停车免费吗？
- 期望：{"expected_doc_ids": ["DOC-PARKING"], "expected_points": ["会员企业车辆凭车牌白名单免费入场", "每日首次入场 4 小时内免费"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "会员企业车辆停车凭车牌白名单免费入场，在地库 B1 与 B2 层停放，每日首次入场 4 小时内免费",
      "访客车辆停车收费按地库入口公示的标准执行"
    ],
    "cited_doc_ids": [
      "DOC-PARKING"
    ],
    "first_token_ms": 0.1,
    "refused": false,
    "total_ms": 0.101
  }
  ```
- 判定：missing expected points: ['会员企业车辆凭车牌白名单免费入场']
- 原因分类：point_miss
- 修复类别：answer-composition

## 4. KB-SPC-002

- 问题/路由：访客车辆停车怎么收费？
- 期望：{"expected_doc_ids": ["DOC-PARKING"], "expected_points": ["按地库入口公示的标准计时收费"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "会员企业车辆停车凭车牌白名单免费入场，在地库 B1 与 B2 层停放，每日首次入场 4 小时内免费",
      "访客车辆停车收费按地库入口公示的标准执行"
    ],
    "cited_doc_ids": [
      "DOC-PARKING"
    ],
    "first_token_ms": 0.137,
    "refused": false,
    "total_ms": 0.137
  }
  ```
- 判定：missing expected points: ['按地库入口公示的标准计时收费']
- 原因分类：point_miss
- 修复类别：answer-composition

## 5. KB-SPC-003

- 问题/路由：会员车停在哪几层？
- 期望：{"expected_doc_ids": ["DOC-PARKING"], "expected_points": ["地库 B1 与 B2 层"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "旗舰会员享独立储物柜一间，另享每月 4 小时免费会议室时长与招商资源对接优先排期",
      "标准会员每月 1 小时免费会议室时长与公共储物柜使用；标准会员使用公共储物柜",
      "储物柜申请按会员等级对应配置",
      "权益适用于会员企业在册员工，由企业管理员维护在册名单",
      "年费标准：标准会员年费 6800 元/年，旗舰会员年费 12800 元/年",
      "会员等级每年评定一次，由运营部根据上一年度使用情况确定",
      "年费如有调整提前 30 天在会员端公告",
      "入驻材料：新会员入驻须提交营业执照复印件、经办人名片与入会申请表"
    ],
    "cited_doc_ids": [
      "DOC-BENEFIT"
    ],
    "first_token_ms": 0.15,
    "refused": false,
    "total_ms": 0.151
  }
  ```
- 判定：missing expected points: ['地库 B1 与 B2 层']；citations outside annotated set: ['DOC-BENEFIT']
- 原因分类：citation_id_mismatch
- 修复类别：retrieval-filter-tightening

## 6. KB-SPC-008

- 问题/路由：会议室有有线网口吗？
- 期望：{"expected_doc_ids": ["DOC-NETWORK"], "expected_points": ["会议室桌面提供有线网口", "接入后自动获取地址"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "会议室预订统一在小程序办理",
      "会议室仅限本企业预订，跨企业使用须由对方会员账号自行预订",
      "现场使用：会议结束后请白板擦净并关闭设备，桌椅恢复原位",
      "设备使用：投屏可使用桌面 HDMI 线或无线投屏器，配对码显示在屏幕右上角；视频会议终端开机后选择预定的会议号接入，使用完毕关机并归位遥控器"
    ],
    "cited_doc_ids": [
      "SOP-ROOM"
    ],
    "first_token_ms": 0.104,
    "refused": false,
    "total_ms": 0.105
  }
  ```
- 判定：missing expected points: ['会议室桌面提供有线网口', '接入后自动获取地址']；citations outside annotated set: ['SOP-ROOM']
- 原因分类：citation_id_mismatch
- 修复类别：retrieval-filter-tightening

## 7. KB-SPC-015

- 问题/路由：咖啡券可以给别人用吗？
- 期望：{"expected_doc_ids": ["DOC-WATERBAR"], "expected_points": ["券仅限本人使用"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "咖啡券：咖啡单次券 30 元/张，十次券 260 元/套"
    ],
    "cited_doc_ids": [
      "DOC-WATERBAR"
    ],
    "first_token_ms": 0.112,
    "refused": false,
    "total_ms": 0.113
  }
  ```
- 判定：missing expected points: ['券仅限本人使用']
- 原因分类：point_miss
- 修复类别：answer-composition

## 8. KB-BEN-005

- 问题/路由：超出的会议室时长怎么算？
- 期望：{"expected_doc_ids": ["DOC-BENEFIT"], "expected_points": ["超出部分按会议室时租标准计费"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "会议室预订统一在小程序办理",
      "会议室仅限本企业预订，跨企业使用须由对方会员账号自行预订",
      "现场使用：会议结束后请白板擦净并关闭设备，桌椅恢复原位",
      "设备使用：投屏可使用桌面 HDMI 线或无线投屏器，配对码显示在屏幕右上角；视频会议终端开机后选择预定的会议号接入，使用完毕关机并归位遥控器",
      "临时加长使用时间须联系前台确认空闲时段，经确认后系统补录时长"
    ],
    "cited_doc_ids": [
      "SOP-ROOM"
    ],
    "first_token_ms": 0.146,
    "refused": false,
    "total_ms": 0.146
  }
  ```
- 判定：missing expected points: ['超出部分按会议室时租标准计费']；citations outside annotated set: ['SOP-ROOM']
- 原因分类：citation_id_mismatch
- 修复类别：retrieval-filter-tightening

## 9. KB-BEN-013

- 问题/路由：单次咖啡券多少钱？
- 期望：{"expected_doc_ids": ["DOC-COUPON"], "expected_points": ["咖啡单次券售价 30 元/张"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "咖啡券：咖啡单次券 30 元/张，十次券 260 元/套"
    ],
    "cited_doc_ids": [
      "DOC-WATERBAR"
    ],
    "first_token_ms": 0.117,
    "refused": false,
    "total_ms": 0.118
  }
  ```
- 判定：missing expected points: ['咖啡单次券售价 30 元/张']；citations outside annotated set: ['DOC-WATERBAR']
- 原因分类：citation_id_mismatch
- 修复类别：retrieval-filter-tightening

## 10. KB-BEN-014

- 问题/路由：券能退吗？
- 期望：{"expected_doc_ids": ["DOC-COUPON"], "expected_points": ["未使用的券可在购买后 7 天内原渠道退回"]}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [],
    "cited_doc_ids": [],
    "first_token_ms": 0.033,
    "refused": true,
    "total_ms": 0.034
  }
  ```
- 判定：answerable item was refused；missing expected points: ['未使用的券可在购买后 7 天内原渠道退回']
- 原因分类：point_miss
- 修复类别：answer-composition

## 11. KB-NA-011

- 问题/路由：物业保洁的排班表能查吗？
- 期望：{"answerable": false}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "answer_points": [
      "法定节假日安排另行公告，由物业提前 3 天在会员端发布",
      "白名单申请：企业管理员在小程序提交车牌，物业复核后加入白名单",
      "报修入口：在小程序报修入口提交工单，IT 或物业 30 分钟内响应",
      "紧急通道：紧急故障拨打物业值班电话，同步在小程序补录工单",
      "工单修改：处理前可在小程序撤回重报，已派单的工单联系物业修改"
    ],
    "cited_doc_ids": [
      "DOC-HOURS"
    ],
    "first_token_ms": 0.162,
    "refused": false,
    "total_ms": 0.163
  }
  ```
- 判定：no-answer item was answered instead of refused
- 原因分类：missed_refusal
- 修复类别：refusal-gate

## 12. RT-ROOM-001

- 问题/路由：帮我把明天下午两点的翠竹厅订一下
- 期望：{"expected_params": {"date": "明天", "room": "翠竹厅", "start": "14:00"}, "expected_tool": "room_book"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.049,
    "params": {
      "date": "明天",
      "room": "翠竹厅",
      "start": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 0.049
  }
  ```
- 判定：parameter mismatch: got {'room': '翠竹厅', 'date': '明天', 'start': ''}, expected {'date': '明天', 'room': '翠竹厅', 'start': '14:00'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 13. RT-ROOM-002

- 问题/路由：预订 12 月 1 日上午十点的兰亭会议室
- 期望：{"expected_params": {"date": "2026-12-01", "room": "兰亭", "start": "10:00"}, "expected_tool": "room_book"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.032,
    "params": {
      "date": "",
      "room": "兰亭",
      "start": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 0.033
  }
  ```
- 判定：parameter mismatch: got {'room': '兰亭', 'date': '', 'start': ''}, expected {'date': '2026-12-01', 'room': '兰亭', 'start': '10:00'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 14. RT-ROOM-003

- 问题/路由：周四下午三点后我要用大会议室一小时
- 期望：{"expected_params": {"date": "周四", "room": "大会议室", "start": "15:00"}, "expected_tool": "room_book"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.023,
    "params": {
      "date": "周四",
      "room": "大会议室",
      "start": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 0.023
  }
  ```
- 判定：parameter mismatch: got {'room': '大会议室', 'date': '周四', 'start': ''}, expected {'date': '周四', 'room': '大会议室', 'start': '15:00'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 15. RT-ROOM-004

- 问题/路由：帮客服部订周五上午九点的第一会议室
- 期望：{"expected_params": {"date": "周五", "room": "第一会议室", "start": "09:00"}, "expected_tool": "room_book"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.02,
    "params": {
      "date": "周五",
      "room": "第一会议室",
      "start": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 0.02
  }
  ```
- 判定：parameter mismatch: got {'room': '第一会议室', 'date': '周五', 'start': ''}, expected {'date': '周五', 'room': '第一会议室', 'start': '09:00'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 16. RT-ROOM-006

- 问题/路由：取消我明天的会议室预订
- 期望：{"expected_params": {"date": "明天", "room": "我的预订", "start": "取消"}, "expected_tool": "room_book"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.016,
    "params": {
      "date": "明天",
      "room": "",
      "start": "取消"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 0.017
  }
  ```
- 判定：parameter mismatch: got {'room': '', 'date': '明天', 'start': '取消'}, expected {'date': '明天', 'room': '我的预订', 'start': '取消'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 17. RT-VIS-005

- 问题/路由：我替临时来访的客户补录一个访客登记
- 期望：{"expected_params": {"visit_date": "今天", "visitor_name": "来访客户"}, "expected_tool": "visitor_register"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.015,
    "params": {
      "visit_date": "",
      "visitor_name": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "visitor_register",
    "total_ms": 0.016
  }
  ```
- 判定：parameter mismatch: got {'visitor_name': '', 'visit_date': ''}, expected {'visit_date': '今天', 'visitor_name': '来访客户'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 18. RT-REP-001

- 问题/路由：301 会议室投影仪没信号，帮我报修
- 期望：{"expected_params": {"issue": "投影仪无信号", "location": "301 会议室"}, "expected_tool": "repair_ticket"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.017,
    "params": {
      "issue": "",
      "location": "301 会议室"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "repair_ticket",
    "total_ms": 0.018
  }
  ```
- 判定：parameter mismatch: got {'location': '301 会议室', 'issue': ''}, expected {'issue': '投影仪无信号', 'location': '301 会议室'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 19. RT-REP-002

- 问题/路由：我们工位的灯闪烁，提个报修单
- 期望：{"expected_params": {"issue": "灯光闪烁", "location": "本企业工位"}, "expected_tool": "repair_ticket"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.016,
    "params": {
      "issue": "",
      "location": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "repair_ticket",
    "total_ms": 0.017
  }
  ```
- 判定：parameter mismatch: got {'location': '', 'issue': ''}, expected {'issue': '灯光闪烁', 'location': '本企业工位'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 20. RT-REP-004

- 问题/路由：我上一张报修单想看下处理进度
- 期望：{"expected_params": {"issue": "进度查询", "location": "我的工单"}, "expected_tool": "repair_ticket"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.013,
    "params": {
      "issue": "",
      "location": ""
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "repair_ticket",
    "total_ms": 0.013
  }
  ```
- 判定：parameter mismatch: got {'location': '', 'issue': ''}, expected {'issue': '进度查询', 'location': '我的工单'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 21. RT-REP-005

- 问题/路由：二楼打印间卡纸了，帮我报修
- 期望：{"expected_params": {"issue": "打印机卡纸", "location": "二楼打印间"}, "expected_tool": "repair_ticket"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.014,
    "params": {
      "issue": "",
      "location": "二楼打印间"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "repair_ticket",
    "total_ms": 0.014
  }
  ```
- 判定：parameter mismatch: got {'location': '二楼打印间', 'issue': ''}, expected {'issue': '打印机卡纸', 'location': '二楼打印间'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 22. RT-REP-006

- 问题/路由：会议室门禁刷不开，提一个紧急报修
- 期望：{"expected_params": {"issue": "门禁失效", "location": "会议室门禁"}, "expected_tool": "repair_ticket"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.014,
    "params": {
      "issue": "",
      "location": "会议室门禁"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "repair_ticket",
    "total_ms": 0.014
  }
  ```
- 判定：parameter mismatch: got {'location': '会议室门禁', 'issue': ''}, expected {'issue': '门禁失效', 'location': '会议室门禁'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 23. RT-REP-007

- 问题/路由：把上午那张报修单的位置改成 B2 停车场
- 期望：{"expected_params": {"issue": "修改工单位置", "location": "B2 停车场"}, "expected_tool": "repair_ticket"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.013,
    "params": {
      "issue": "",
      "location": "B2 停车场"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "repair_ticket",
    "total_ms": 0.014
  }
  ```
- 判定：parameter mismatch: got {'location': 'B2 停车场', 'issue': ''}, expected {'issue': '修改工单位置', 'location': 'B2 停车场'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 24. RT-ANN-001

- 问题/路由：在本企业频道发一条通知：周五下午团建
- 期望：{"expected_params": {"channel": "本企业频道", "title": "周五下午团建通知"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.014,
    "params": {
      "channel": "本企业频道",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.015
  }
  ```
- 判定：parameter mismatch: got {'channel': '本企业频道', 'title': '公告'}, expected {'channel': '本企业频道', 'title': '周五下午团建通知'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 25. RT-ANN-002

- 问题/路由：给全体员工发个公告：明天消防演习
- 期望：{"expected_params": {"channel": "全体员工", "title": "消防演习公告"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.014,
    "params": {
      "channel": "全体员工",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.014
  }
  ```
- 判定：parameter mismatch: got {'channel': '全体员工', 'title': '公告'}, expected {'channel': '全体员工', 'title': '消防演习公告'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 26. RT-ANN-003

- 问题/路由：在我们部门群发一条放假安排通知
- 期望：{"expected_params": {"channel": "本部门", "title": "放假安排通知"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.013,
    "params": {
      "channel": "",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.013
  }
  ```
- 判定：parameter mismatch: got {'channel': '', 'title': '公告'}, expected {'channel': '本部门', 'title': '放假安排通知'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 27. RT-ANN-004

- 问题/路由：帮我把昨天的公告撤回来
- 期望：{"expected_params": {"channel": "我的公告", "title": "撤回昨日公告"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.011,
    "params": {
      "channel": "",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.012
  }
  ```
- 判定：parameter mismatch: got {'channel': '', 'title': '公告'}, expected {'channel': '我的公告', 'title': '撤回昨日公告'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 28. RT-ANN-005

- 问题/路由：在会员动态里发一条我们公司的乔迁喜讯
- 期望：{"expected_params": {"channel": "会员动态", "title": "乔迁喜讯"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.013,
    "params": {
      "channel": "会员动态",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.013
  }
  ```
- 判定：parameter mismatch: got {'channel': '会员动态', 'title': '公告'}, expected {'channel': '会员动态', 'title': '乔迁喜讯'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 29. RT-ANN-006

- 问题/路由：给行政组发一条资产盘点通知
- 期望：{"expected_params": {"channel": "行政组", "title": "资产盘点通知"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.012,
    "params": {
      "channel": "行政组",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.012
  }
  ```
- 判定：parameter mismatch: got {'channel': '行政组', 'title': '公告'}, expected {'channel': '行政组', 'title': '资产盘点通知'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 30. RT-ANN-007

- 问题/路由：帮我把公告里的错别字改一下重新发
- 期望：{"expected_params": {"channel": "我的公告", "title": "修订重发公告"}, "expected_tool": "announce_send"}
- 错误输出（被测作答方实际输出，逐字）：
  ```json
  {
    "first_token_ms": 0.012,
    "params": {
      "channel": "",
      "title": "公告"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 0.012
  }
  ```
- 判定：parameter mismatch: got {'channel': '', 'title': '公告'}, expected {'channel': '我的公告', 'title': '修订重发公告'}
- 原因分类：parameter_error
- 修复类别：slot-filling

## 根因分类汇总

| 原因分类 | 条数 |
|---|---|
| parameter_error | 19 |
| point_miss | 6 |
| citation_id_mismatch | 4 |
| missed_refusal | 1 |
