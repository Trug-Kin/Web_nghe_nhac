-- Script để cập nhật ảnh cho các bài hát
-- Chạy trong MySQL Workbench và nhớ COMMIT!

USE flask_web;

-- Bật autocommit hoặc bắt đầu transaction
START TRANSACTION;

-- Cập nhật ảnh cho các bài hát
UPDATE songs SET image_path = 'images/songs/noi_nay_co_anh.jpg' WHERE id = 1;
UPDATE songs SET image_path = 'images/songs/lac_troi.jpg' WHERE id = 2;
UPDATE songs SET image_path = 'images/songs/chung_ta_khong_thuoc_ve_nhau.jpg' WHERE id = 3;
UPDATE songs SET image_path = 'images/songs/chac_ai_do_se_ve.jpg' WHERE id = 4;
UPDATE songs SET image_path = 'images/songs/hay_trao_cho_anh.jpg' WHERE id = 6;
UPDATE songs SET image_path = 'images/songs/chay_ngay_di.jpg' WHERE id = 7;
UPDATE songs SET image_path = 'images/songs/vung_an_toan.jpg' WHERE id = 8;
UPDATE songs SET image_path = 'images/songs/the_one.jpg' WHERE id = 9;
UPDATE songs SET image_path = 'images/songs/viet_em_ban_tinh_ca.jpg' WHERE id = 10;

-- LƯU THAY ĐỔI
COMMIT;

-- Kiểm tra kết quả
SELECT id, title, image_path FROM songs WHERE id IN (1,2,3,4,6,7,8,9,10);
