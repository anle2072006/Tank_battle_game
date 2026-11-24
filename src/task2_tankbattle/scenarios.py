from engine import GameState, Tank, Base

class MapBuilder:
    """
    Xây dựng bản đồ từ lưới ký tự (Grid String) giúp dễ dàng thiết kế kịch bản:
    '.' : Ô trống
    '#' : Tường gạch (HP = 3)
    'A' : Căn cứ (Base) người chơi 1 (HP = 9)
    'B' : Căn cứ (Base) người chơi 2 (HP = 9)
    '1' : Xe tăng người chơi 1 (HP = 6)
    '2' : Xe tăng người chơi 2 (HP = 6)
    """
    @staticmethod
    def from_grid(grid_lines: list[str], p1_dir="DOWN", p2_dir="UP", 
                  p1_hp=6, p2_hp=6, base_hp=9) -> GameState:
        height = len(grid_lines)
        width = len(grid_lines[0])
        tanks = {}
        bases = {}
        walls = {}

        for y, row in enumerate(grid_lines):
            for x, ch in enumerate(row):
                if ch == '#':
                    walls[(x, y)] = 3
                elif ch == '1':
                    tanks[1] = Tank(1, x, y, direction=p1_dir, hp=p1_hp)
                elif ch == '2':
                    tanks[2] = Tank(2, x, y, direction=p2_dir, hp=p2_hp)
                elif ch == 'A':  # Base 1
                    bases[1] = Base(1, x, y, hp=base_hp)
                elif ch == 'B':  # Base 2
                    bases[2] = Base(2, x, y, hp=base_hp)

        return GameState(width, height, tanks, bases, walls, bullets=[], current_turn=1)

    @staticmethod
    def get_endgame_scenario() -> GameState:
        """
        Kịch bản 1 (Endgame): Bản đồ 7x5 đối xứng tâm, mô phỏng tàn cuộc quyết định
        (Tank 2 HP, Base 2 HP). Ở độ sâu d <= 4, chỉ Heuristic nhận ra lợi thế của
        MOVE_DOWN (nên trên GUI d=4, nếu P1 dùng AI thuần gặp P2 Heuristic thì P2 thắng);
        tại d = 5, cả 4 thuật toán đều nhìn thấy trạng thái kết thúc và chọn MOVE_DOWN.
        """
        grid = [
            ".A.....",
            "..#..1.",
            "...#...",
            ".2..#..",
            ".....B."
        ]
        return MapBuilder.from_grid(grid, p1_dir="LEFT", p2_dir="RIGHT", p1_hp=2, p2_hp=2, base_hp=2)

    @staticmethod
    def get_midgame_scenario() -> GameState:
        """
        Kịch bản 2 (Mid-game): Bản đồ đối xứng tâm có tường chắn bảo vệ Base.
        """
        grid = [
            "....A....",
            "...###...",
            "...1.....",
            ".##...##.",
            "....#....",
            ".##...##.",
            ".....2...",
            "...###...",
            "....B...."
        ]
        return MapBuilder.from_grid(grid, p1_dir="DOWN", p2_dir="UP", p1_hp=6, p2_hp=6)
    
    @staticmethod
    def get_battle_city_map() -> GameState:
        # Ban do kich thuoc 13x13 mo phong man choi Battle City co dien (doi xung tam).
        # Ky hieu: 'A', 'B' la can cu (HP=9); '1', '2' la xe tang (HP=6); '#' la tuong gach (HP=3).
        grid = [
            ".....#A#.....",
            "..#..###..#..",
            "..#.1.....#..",
            "..#..###..#..",
            ".............",
            "###..###..###",
            "..#.......#..",
            "###..###..###",
            ".............",
            "..#..###..#..",
            "..#.....2.#..",
            "..#..###..#..",
            ".....#B#....."
        ]
        return MapBuilder.from_grid(grid, p1_dir="DOWN", p2_dir="UP", p1_hp=6, p2_hp=6)