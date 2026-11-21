from engine import GameState, Tank, Base, Bullet

class MapBuilder:
    """
    Xây dựng bản đồ từ lưới ký tự (Grid String) giúp dễ dàng thiết kế kịch bản:
    '.' : Ô trống
    '#' : Tường gạch (HP = 3)
    'B1': Base người chơi 1 (HP = 9)
    'B2': Base người chơi 2 (HP = 9)
    'T1': Xe tăng người chơi 1 (HP = 6)
    'T2': Xe tăng người chơi 2 (HP = 6)
    """
    @staticmethod
    def from_grid(grid_lines: list[str], p1_dir="DOWN", p2_dir="UP", 
                  p1_hp=6, p2_hp=6) -> GameState:
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
                    bases[1] = Base(1, x, y, hp=9)
                elif ch == 'B':  # Base 2
                    bases[2] = Base(2, x, y, hp=9)

        return GameState(width, height, tanks, bases, walls, bullets=[], current_turn=1)

    @staticmethod
    def get_endgame_scenario() -> GameState:
        """
        Kịch bản 1 (Endgame): 2 xe tăng chỉ còn 1 HP và đứng gần nhau.
        Giúp Minimax thuần và Alpha-Beta thuần chạm tới Terminal State ở độ sâu d = 3, 4.
        """
        grid = [
            "...A...",
            ".......",
            "..1.#..",
            "....2..",
            ".......",
            "...B..."
        ]
        return MapBuilder.from_grid(grid, p1_dir="DOWN", p2_dir="LEFT", p1_hp=1, p2_hp=1)

    @staticmethod
    def get_midgame_scenario() -> GameState:
        """
        Kịch bản 2 (Mid-game): Bản đồ đối xứng chuẩn có tường chắn bảo vệ Base.
        """
        grid = [
            "....A....",
            "...###...",
            "....1....",
            ".##...##.",
            "....#....",
            ".##...##.",
            "....2....",
            "...###...",
            "....B...."
        ]
        return MapBuilder.from_grid(grid, p1_dir="DOWN", p2_dir="UP", p1_hp=6, p2_hp=6)
    
    @staticmethod
    def get_battle_city_map() -> GameState:
        # Ban do kich thuoc 13x13 mo phong man choi Battle City co dien.
        # Ky hieu: 'A', 'B' la căn cứ (HP=9); '1', '2' la xe tang (HP=6); '#' la tuong gach (HP=3).
        grid = [
            ".....#A#.....",
            "..#..###..#..",
            "..#...1...#..",
            "..#..###..#..",
            ".............",
            "###..###..###",
            "..#.......#..",
            "###..###..###",
            ".............",
            "..#..###..#..",
            "..#...2...#..",
            "..#..###..#..",
            ".....#B#....."
        ]
        return MapBuilder.from_grid(grid, p1_dir="DOWN", p2_dir="UP", p1_hp=6, p2_hp=6)