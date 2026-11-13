G = (None, None)

# Bảng 5x5 mẫu trong đề
SAMPLE_5X5 = [
    [G, G, (None, 21), (None, 14), G],
    [G, (12, 14), 0, 0, (None, 11)],
    [(21, None), 0, 0, 0, 0],
    [(11, None), 0, 0, 0, 0],
    [G, (16, None), 0, 0, G],
]

# Bảng 9x9 phức tạp trong đề (48 ô trắng, 28 run, tổng ngang = tổng dọc = 249)
SAMPLE_9X9 = [
    [G, G, (None, 44), (None, 16), (None, 9), G, (None, 15), (None, 44), G],
    [G, (22, None), 0, 0, 0, (3, 11), 0, 0, (None, 14)],
    [G, (28, 17), 0, 0, 0, 0, 0, 0, 0],
    [(14, None), 0, 0, G, (20, 12), 0, 0, 0, 0],
    [(17, None), 0, 0, (22, 29), 0, 0, 0, 0, (None, 7)],
    [G, (28, 12), 0, 0, 0, 0, (12, None), 0, 0],
    [(14, None), 0, 0, 0, 0, (None, 7), (6, 12), 0, 0],
    [(39, None), 0, 0, 0, 0, 0, 0, 0, G],
    [G, (16, None), 0, 0, (8, None), 0, 0, 0, G],
]

# Vô nghiệm ngay ở mức tổ hợp: một ô đơn có tổng 16 (> 9)
UNSOLVABLE_COMBO = [
    [G, (None, 3)],
    [(16, None), 0],
    [G, 0],
]

# Vô nghiệm nhưng từng run riêng lẻ vẫn có tổ hợp, nên solver phải tìm kiếm mới phát hiện
# Hàng: 3, 3. Cột: 3, 4 (tổng hàng 6 khác tổng cột 7)
UNSOLVABLE_SEARCH = [
    [G, (None, 3), (None, 4)],
    [(3, None), 0, 0],
    [(3, None), 0, 0],
]

# Có đúng 2 nghiệm: (1,2 / 2,1) và (2,1 / 1,2)
MULTI_SOLUTION = [
    [G, (None, 3), (None, 3)],
    [(3, None), 0, 0],
    [(3, None), 0, 0],
]
