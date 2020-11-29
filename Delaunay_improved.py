from random import random as r
from random import randint as rr


class Triangle:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        print(self.a, self.b, self.c)
        return "  "


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.e = None
        self.prv = None
        self.nxt = None
        self.color = None

    def __str__(self):
        return str((self.x, self.y))


class HalfEdge:
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
        self.prv = None
        self.nxt = None
        self.twin = None
        self.is_deleted = False
        self.is_external_face = False

    def __str__(self):
        return str((self.v1.x, self.v1.y)) + "," + str((self.v2.x, self.v2.y))


def square_of_dist(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return dx ** 2 + dy ** 2


def sign_area(p1, p2, p3):
    predicate = (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x)
    if predicate < 0:
        return -1
    elif predicate == 0:
        return 0
    return 1


def get_normal(p1, p2):
    x_m = (p1.x + p2.x) / 2
    y_m = (p1.y + p2.y) / 2
    a = p2.x - p1.x
    b = p2.y - p1.y
    c = -(a * x_m + b * y_m)
    return a, b, c


def intersect(a1, b1, c1, a2, b2, c2):
    d = (a1 * b2 - a2 * b1)
    x = (c2 * b1 - c1 * b2) / d
    y = (a2 * c1 - a1 * c2) / d
    return x, y


def get_circle(p1, p2, p3):
    a1, b1, c1 = get_normal(p1, p2)
    a2, b2, c2 = get_normal(p2, p3)
    cx, cy = intersect(a1, b1, c1, a2, b2, c2)
    r_square = square_of_dist(p1, Point(cx, cy))
    return cx, cy, r_square


def add_to_cache(cache_data, t):
    cache, curr_size, w, h = cache_data["cache"], cache_data["curr_size"], cache_data["w"], cache_data["h"]
    sw = w / curr_size
    sh = h / curr_size
    a, b, c = t.a, t.b, t.c
    c_x = (a.x + b.x + c.x) / 3
    c_y = (a.y + b.y + c.y) / 3
    cache[int(c_x / sw)][int(c_y / sh)] = t


def update_cache(cache_data):
    cache, curr_size = cache_data["cache"], cache_data["curr_size"]
    new_size = curr_size * 2
    new_cache = [[0] * new_size for _ in range(new_size)]
    for i in range(curr_size):
        for j in range(curr_size):
            new_cache[2 * i][2 * j] = cache[i][j]
            new_cache[2 * i][2 * j + 1] = cache[i][j]
            new_cache[2 * i + 1][2 * j] = cache[i][j]
            new_cache[2 * i + 1][2 * j + 1] = cache[i][j]
    return new_size, new_cache


def get_cos(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    k = 1 if dx > 0 else -1
    return k * dx ** 2 / (dx ** 2 + dy ** 2)


def get_ch(p):
    p0 = p[0]
    p0_i = 0
    for i in range(len(p)):
        if p[i].y < p0.y or (p[i].y == p0.y and p[i].x < p0.x):
            p0 = p[i]
            p0_i = i
    p[-1], p[p0_i] = p[p0_i], p[-1]
    p.pop()
    p.sort(key=lambda pt: square_of_dist(p0, pt))
    p.sort(key=lambda pt: get_cos(p0, pt), reverse=True)
    ch = [p0, p[0]]

    other_points = []
    l = 2
    for i in range(1, len(p)):
        while l >= 2:
            if sign_area(ch[-2], ch[-1], p[i]) != 1:
                other_points.append(ch.pop())
                l -= 1
            else:
                break
        ch.append(p[i])
        l += 1
    return ch, other_points


def ch_triangulation(p, he, cache_data):
    ch, other_points = get_ch(p)

    for i in range(len(ch)):
        ch[i].prv = ch[i - 1]
        ch[i - 1].nxt = ch[i]
    curr = ch[0]
    while curr.nxt.nxt.nxt != curr:
        get_triangle(curr.prv, curr, curr.nxt, he, cache_data)
        check_Delaunay_condition(curr.prv, curr, he, cache_data)
        curr.prv.nxt = curr.nxt
        curr.nxt.prv = curr.prv
        curr = curr.nxt
    get_triangle(curr, curr.nxt, curr.prv, he, cache_data)
    check_Delaunay_condition(curr.prv, curr, he, cache_data)
    cache_data["curr_size"], cache_data["cache"] = update_cache(cache_data)
    return ch, other_points


def triangle_predicate(p1, p2, p3, p):
    a, b, c = sign_area(p1, p2, p), sign_area(p2, p3, p), sign_area(p3, p1, p)
    if a == b == c:
        return 1
    if a == 0 or b == 0 or c == 0:
        return 2
    return 0


def update_triangle(a, b, c, a1, b1, c1, triangles):
    for u, v, w in ((a, b, c), (c, a, b), (b, c, a)):
        if triangles.get((u, v, w)):
            t = triangles.pop((u, v, w))
            triangles[(a1, b1, c1)] = t
            t.a, t.b, t.c = a1, b1, c1
            return


def get_triangle(a, b, c, he, cache_data):
    triangles = cache_data["triangles"]
    if sign_area(a, b, c) != 1:
        a, c = c, a

    e = []
    for u, v in ((a, b), (b, c), (c, a)):
        if not he.get((u, v)):
            he[(u, v)] = HalfEdge(u, v)
        e.append(he[(u, v)])

        if he.get((v, u)):
            he[(u, v)].twin = he[(v, u)]
            he[(v, u)].twin = he[(u, v)]
        u.e = he[(u, v)]

    for i in range(3):
        e[i].prv, e[i - 1].nxt = e[i - 1], e[i]
    if not triangles.get((a, b, c)):
        triangles[(a, b, c)] = Triangle(a, b, c)
        add_to_cache(cache_data, triangles[(a, b, c)])


def flip_edge(v1, v2, he, cache_data):
    triangles = cache_data["triangles"]
    p1, p2 = he[(v1, v2)].nxt.v2, he[(v2, v1)].nxt.v2
    he.pop((v1, v2))
    he.pop((v2, v1))
    update_triangle(v1, v2, p1, p1, p2, v2, triangles)
    update_triangle(v2, v1, p2, p2, p1, v1, triangles)
    add_to_cache(cache_data, triangles[(p1, p2, v2)])
    add_to_cache(cache_data, triangles[(p2, p1, v1)])
    get_triangle(p1, p2, v2, he, cache_data)
    get_triangle(p2, p1, v1, he, cache_data)


def find_triangle(p, he, cache_data):
    cache, curr_size, w, h = cache_data["cache"], cache_data["curr_size"], cache_data["w"], cache_data["h"]
    sh = h / curr_size
    sw = w / curr_size
    t = cache[int(p.x / sw)][int(p.y / sh)]
    a, b, c = t.a, t.b, t.c
    case = triangle_predicate(a, b, c, p)
    while not case:
        for u, v in ((a, b), (b, c), (c, a)):
            w = he[(u, v)].nxt.v2
            a1, a2 = sign_area(u, v, p), sign_area(u, v, w)
            if a1 != a2:
                a, b, c = v, u, he[(v, u)].nxt.v2
                case = triangle_predicate(a, b, c, p)
                break
    return case, a, b, c


def insert_point(p, he, cache_data):
    triangles = cache_data["triangles"]
    case, a, b, c = find_triangle(p, he, cache_data)
    if case == 1:
        update_triangle(a, b, c, a, b, p, triangles)
        for u, v in ((a, b), (b, c), (c, a)):
            get_triangle(u, v, p, he, cache_data)
            check_Delaunay_condition(u, v, he, cache_data)
        return True
    return False


def Delaunay_condition(v1, v2, he):
    p1, p2 = he[(v1, v2)].nxt.v2, he[(v2, v1)].nxt.v2
    cx1, cy1, r1 = get_circle(v1, v2, p1)
    cx2, cy2, r2 = get_circle(v1, v2, p2)
    return square_of_dist(p1, Point(cx2, cy2)) >= r2 and square_of_dist(p2, Point(cx1, cy1)) >= r1


def check_Delaunay_condition(v1, v2, he, cache_data):
    if not he.get((v1, v2)) or not he[(v1, v2)].twin:
        return

    p1, p2 = he[(v1, v2)].nxt.v2, he[(v2, v1)].nxt.v2
    if not Delaunay_condition(v1, v2, he):
        flip_edge(v1, v2, he, cache_data)
        for u, v in [(v2, p1), (p1, v1), (v1, p2), (p2, v2)]:
            check_Delaunay_condition(u, v, he, cache_data)


def get_external_face(ch, he):
    l = len(ch)
    for i in range(l - 1, -1, -1):
        p1 = ch[i]
        p2 = ch[(i - 1) % l]
        e1 = HalfEdge(p1, p2)
        e1.is_external_face = True
        he[(e1.v1, e1.v2)] = e1
        if i <= l - 2:
            e2 = he[(ch[i + 1], ch[i])]
            e1.prv, e2.nxt = e2, e1
        e1.twin, he[(p2, p1)].twin = he[(p2, p1)], e1
    he[(ch[l - 1], ch[l - 2])].prv = he[(ch[0], ch[l - 1])]
    he[(ch[0], ch[l - 1])].nxt = he[(ch[l - 1], ch[l - 2])]


def Delaunay_triangulation(p, w, h):
    he = {}
    added = []
    curr_size = 1
    cache = [[0] * curr_size for _ in range(curr_size)]
    width, height = w, h
    cache_data = {"cache": cache, "curr_size": curr_size, "w": width, "h": height, "k": 5, "triangles": {}}
    ch, other_points = ch_triangulation(p, he, cache_data)
    cnt = 0
    for pt in other_points:
        is_added = insert_point(pt, he, cache_data)
        if is_added:
            cnt += 1
            added.append(pt)
        if cnt > cache_data["k"] * cache_data["curr_size"] ** 2:
            cache_data["curr_size"], cache_data["cache"] = update_cache(cache_data)

    get_external_face(ch, he)
    return he, added + ch, cache_data["triangles"]


def get_neighbors(pt):
    e = pt.e
    curr = e.prv.twin
    g = [curr.v2]
    while curr != e:
        curr = curr.prv.twin
        g.append(curr.v2)
    return g


def get_graph(p):
    g = {pt: [] for pt in p}
    for pt in p:
        g[pt] = get_neighbors(pt)
    return g


def bfs(g, v):
    used = {}
    q = [v]
    while q:
        curr = q.pop()
        used[curr] = True
        for u in g[curr]:
            if not used.get(u):
                q.append(u)


def set_colors(triangles):
    for key in triangles:
        t = triangles[key]
        a = t.a
        b = t.b
        c = t.c
        a.color = rr(1, 3)
        b.color = rr(1, 3)
        c.color = rr(1, 3)


def Urquhart_graph(triangles, he):
    for key in triangles:
        t = triangles[key]
        e1 = he[(t.a, t.b)]
        e2 = e1.nxt
        e3 = e2.nxt
        d = [square_of_dist(e.v1, e.v2) for e in (e1, e2, e3)]
        mn = max(d)
        (e1, e2, e3)[d.index(mn)].is_deleted = True


def quasi_random2d(n, box):
    seed = r()
    g = 1.32471795724474602596
    a1 = 1.0 / g
    a2 = 1.0 / (g * g)
    p = []
    for i in range(n):
        x = (seed + a1 * (i + 1)) % 1
        y = (seed + a2 * (i + 1)) % 1
        x = int(x * (box[1] - box[0]) + box[0])
        y = int(y * (box[3] - box[2]) + box[2])
        p.append(Point(x, y))
    return p
