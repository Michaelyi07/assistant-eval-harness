# 首轮典型错误分析

错误条目共 11 条（首轮运行由 run_eval.py 实际产出，原始错误输出块逐字保留）。

## 1. KB-SOP-011

- 问题/路由：访客车辆入园怎么处理？
- 期望：{"expected_doc_ids": ["SOP-VISITOR", "DOC-PARKING"], "expected_points": ["邀请会员在小程序登记车牌", "访客车辆按地库公示标准计时收费"]}
- 错误输出（原始，逐字）：
  ```json
  {
    "answer_points": [
      "邀请会员在小程序登记车牌",
      "访客车辆按地库公示标准计时收费"
    ],
    "cited_doc_ids": [
      "SOP-VISITOR",
      "DOC-NETWORK"
    ],
    "first_token_ms": 180,
    "refused": false,
    "total_ms": 640
  }
  ```
- 判定：citations outside annotated set: ['DOC-NETWORK']
- 原因分类：citation_id_mismatch
- 修复类别：retrieval-filter-tightening
- 备注：multi-doc answer cited an extra doc outside the annotation

## 2. KB-SOP-014

- 问题/路由：一般投诉多久办结？
- 期望：{"expected_doc_ids": ["SOP-COMPLAINT"], "expected_points": ["一般投诉 3 个工作日内办结", "复杂投诉时限由客户成功部与投诉人确认"]}
- 错误输出（原始，逐字）：
  ```json
  {
    "answer_points": [
      "一般投诉 3 个工作日内办结"
    ],
    "cited_doc_ids": [
      "SOP-COMPLAINT"
    ],
    "first_token_ms": 240,
    "refused": false,
    "total_ms": 910
  }
  ```
- 判定：missing expected points: ['复杂投诉时限由客户成功部与投诉人确认']
- 原因分类：point_miss
- 修复类别：answer-composition
- 备注：second expected point dropped

## 3. KB-SOP-023

- 问题/路由：紧急报修走什么通道？
- 期望：{"expected_doc_ids": ["SOP-REPAIR"], "expected_points": ["拨打物业值班电话", "同步在小程序补录工单"]}
- 错误输出（原始，逐字）：
  ```json
  {
    "answer_points": [],
    "cited_doc_ids": [],
    "first_token_ms": 140,
    "refused": true,
    "total_ms": 820
  }
  ```
- 判定：answerable item was refused；missing expected points: ['拨打物业值班电话', '同步在小程序补录工单']
- 原因分类：boundary_misclassification
- 修复类别：refusal-gate
- 备注：emergency repair channel is documented but was refused

## 4. KB-SPC-013

- 问题/路由：咖啡券多少钱一张？
- 期望：{"expected_doc_ids": ["DOC-WATERBAR"], "expected_points": ["咖啡单次券 30 元/张", "十次券 260 元/套"]}
- 错误输出（原始，逐字）：
  ```json
  {
    "answer_points": [
      "咖啡单次券 30 元/张"
    ],
    "cited_doc_ids": [
      "DOC-WATERBAR"
    ],
    "first_token_ms": 120,
    "refused": false,
    "total_ms": 820
  }
  ```
- 判定：missing expected points: ['十次券 260 元/套']
- 原因分类：point_miss
- 修复类别：answer-composition
- 备注：ten-coupon price point dropped

## 5. KB-BEN-005

- 问题/路由：超出的会议室时长怎么算？
- 期望：{"expected_doc_ids": ["DOC-BENEFIT"], "expected_points": ["超出部分按会议室时租标准计费"]}
- 错误输出（原始，逐字）：
  ```json
  {
    "answer_points": [
      "超出部分按会议室时租标准计费"
    ],
    "cited_doc_ids": [
      "DOC-BENEFIT",
      "DOC-GRADE"
    ],
    "first_token_ms": 220,
    "refused": false,
    "total_ms": 1000
  }
  ```
- 判定：citations outside annotated set: ['DOC-GRADE']
- 原因分类：citation_id_mismatch
- 修复类别：retrieval-filter-tightening
- 备注：cited DOC-GRADE alongside DOC-BENEFIT; DOC-GRADE not annotated

## 6. KB-NA-003

- 问题/路由：翠竹厅最多能容纳多少人？
- 期望：{"answerable": false}
- 错误输出（原始，逐字）：
  ```json
  {
    "answer_points": [
      "翠竹厅最多可容纳 60 人"
    ],
    "cited_doc_ids": [
      "SOP-ROOM"
    ],
    "first_token_ms": 200,
    "refused": false,
    "total_ms": 820
  }
  ```
- 判定：no-answer item was answered instead of refused
- 原因分类：boundary_misclassification
- 修复类别：refusal-gate
- 备注：hall capacity not in KB; answered a guessed figure

## 7. RT-ROOM-002

- 问题/路由：预订 12 月 1 日上午十点的兰亭会议室
- 期望：{"expected_params": {"date": "2026-12-01", "room": "兰亭", "start": "10:00"}, "expected_tool": "room_book"}
- 错误输出（原始，逐字）：
  ```json
  {
    "first_token_ms": 200,
    "params": {
      "date": "01/12/2026",
      "room": "兰亭",
      "start": "10:00"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 730
  }
  ```
- 判定：parameter mismatch: got {'room': '兰亭', 'date': '01/12/2026', 'start': '10:00'}, expected {'date': '2026-12-01', 'room': '兰亭', 'start': '10:00'}
- 原因分类：parameter_slot_error
- 修复类别：slot-filling
- 备注：date normalized incorrectly

## 8. RT-MBR-004

- 问题/路由：查我们企业的储物柜编号
- 期望：{"expected_params": {"field": "储物柜", "member_org": "本企业"}, "expected_tool": "member_lookup"}
- 错误输出（原始，逐字）：
  ```json
  {
    "first_token_ms": 120,
    "params": {
      "field": "年费有效期",
      "member_org": "本企业"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "member_lookup",
    "total_ms": 730
  }
  ```
- 判定：parameter mismatch: got {'member_org': '本企业', 'field': '年费有效期'}, expected {'field': '储物柜', 'member_org': '本企业'}
- 原因分类：parameter_slot_error
- 修复类别：slot-filling
- 备注：field slot filled with wrong value

## 9. RT-VIS-006

- 问题/路由：登记一位访客：周先生，约的是下周一上午
- 期望：{"expected_params": {"visit_date": "下周一", "visitor_name": "周先生"}, "expected_tool": "visitor_register"}
- 错误输出（原始，逐字）：
  ```json
  {
    "first_token_ms": 180,
    "params": {
      "channel": "会员动态",
      "title": "访客登记"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "announce_send",
    "total_ms": 730
  }
  ```
- 判定：tool mismatch: selected 'announce_send', expected 'visitor_register'
- 原因分类：tool_selection_error
- 修复类别：router-training
- 备注：register request routed to announce_send

## 10. RT-REP-006

- 问题/路由：会议室门禁刷不开，提一个紧急报修
- 期望：{"expected_params": {"issue": "门禁失效", "location": "会议室门禁"}, "expected_tool": "repair_ticket"}
- 错误输出（原始，逐字）：
  ```json
  {
    "first_token_ms": 200,
    "params": {
      "date": "今天",
      "room": "会议室门禁",
      "start": "报修"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "room_book",
    "total_ms": 1000
  }
  ```
- 判定：tool mismatch: selected 'room_book', expected 'repair_ticket'
- 原因分类：tool_selection_error
- 修复类别：router-training
- 备注：emergency repair routed to room_book

## 11. RT-ANN-005

- 问题/路由：在会员动态里发一条我们公司的乔迁喜讯
- 期望：{"expected_params": {"channel": "会员动态", "title": "乔迁喜讯"}, "expected_tool": "announce_send"}
- 错误输出（原始，逐字）：
  ```json
  {
    "first_token_ms": 200,
    "params": {
      "field": "会员动态",
      "member_org": "本企业"
    },
    "reject_reason": null,
    "rejected": false,
    "selected_tool": "member_lookup",
    "total_ms": 730
  }
  ```
- 判定：tool mismatch: selected 'member_lookup', expected 'announce_send'
- 原因分类：tool_selection_error
- 修复类别：router-training
- 备注：member-dynamics post routed to member_lookup

## 根因分类汇总

| 原因分类 | 条数 |
|---|---|
| tool_selection_error | 3 |
| citation_id_mismatch | 2 |
| point_miss | 2 |
| boundary_misclassification | 2 |
| parameter_slot_error | 2 |
