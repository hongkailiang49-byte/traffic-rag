export const SLOT_LABELS: Record<string, string> = {
  location: '地点',
  severity: '严重程度',
  casualties: '伤亡情况',
  hazmat: '危化品',
  road_condition: '路面状况',
  tunnel_name: '隧道名称',
  fire_level: '火势等级',
  evacuation_status: '疏散情况',
  device_type: '设备类型',
  impact_scope: '影响范围',
  cause: '拥堵原因',
  scope: '拥堵范围',
}

export const INTENT_SLOTS: Record<string, string[]> = {
  accident: ['location', 'severity', 'casualties', 'hazmat', 'road_condition'],
  fire: ['location', 'tunnel_name', 'fire_level', 'evacuation_status'],
  equipment: ['device_type', 'location', 'impact_scope'],
  congestion: ['location', 'cause', 'scope'],
}

export const INTENT_LABELS: Record<string, string> = {
  accident: '交通事故',
  fire: '火灾',
  equipment: '设备故障',
  congestion: '交通拥堵',
}
