-- 초기 시드 데이터

-- Waste types
INSERT INTO wastetype (type_name) VALUES
  ('MetalCan'),
  ('PetBottle'),
  ('Plastic'),
  ('Styrofoam');

-- Trashcans (도시 3개 서로 다르게)
INSERT INTO trashcan (
  trashcan_name,
  trashcan_capacity,
  current_volume,
  trashcan_city,
  address_detail,
  trashcan_latitude,
  trashcan_longitude,
  is_online,
  server_url
) VALUES
  ('TC_SEOUL_01', 100, 10, 'Seoul', '서울 어딘가 1', 37.5665, 126.9780, 1, 'http://127.0.0.1:8001'),
  ('TC_BUSAN_01', 120, 30, 'Busan', '부산 어딘가 2', 35.1796, 129.0756, 0, 'http://127.0.0.1:8002'),
  ('TC_DAEGU_01', 80, 5, 'Daegu', '대구 어딘가 3', 35.8714, 128.6014, 1, 'http://127.0.0.1:8003');
