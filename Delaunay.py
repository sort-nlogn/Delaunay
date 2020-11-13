from tkinter import *
from random import random as r
from random import randint as rr
from datetime import datetime as dt


class Triangle:
    def __init__(self, e):
        self.e = e


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
    x = (c2 * b1 - c1 * b2) / (a1 * b2 - a2 * b1)
    y = (a2 * c1 - a1 * c2) / (a1 * b2 - a2 * b1)
    return x, y


def get_circle(p1, p2, p3):
    a1, b1, c1 = get_normal(p1, p2)
    a2, b2, c2 = get_normal(p2, p3)
    cx, cy = intersect(a1, b1, c1, a2, b2, c2)
    r_square = square_of_dist(p1, Point(cx, cy))
    return cx, cy, r_square


def add_to_cache(a, b, c, cache_data):
    cache, curr_size, w, h = cache_data["cache"], cache_data["curr_size"], cache_data["w"], cache_data["h"]
    sw = w / curr_size
    sh = h / curr_size

    for pt in (a, b, c):
        cache[int(max(0, pt.x - 1) / sw)][int(max(0, pt.y - 1) / sh)] = (a, b, c)


def change_cache(a, b, c, a1, b1, c1, cache_data):
    cache, curr_size = cache_data["cache"], cache_data["curr_size"]
    for i in range(curr_size):
        for j in range(curr_size):
            if cache[i][j] in ((a, b, c), (b, c, a), (c, a, b)):
                cache[i][j] = (a1, b1, c1)


def update_cache(cache_data):
    cache, curr_size = cache_data["cache"], cache_data["curr_size"]
    new_size = curr_size * 2
    new_cache = [[0] * new_size for i in range(new_size)]
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
    return ch, other_points


def triangle_predicate(p1, p2, p3, p):
    a, b, c = sign_area(p1, p2, p), sign_area(p2, p3, p), sign_area(p3, p1, p)
    if a == b == c:
        return 1
    if a == 0 or b == 0 or c == 0:
        return 2
    return 0


def get_triangle(a, b, c, he, cache_data):
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
    add_to_cache(a, b, c, cache_data)


def flip_edge(v1, v2, he, cache_data):
    p1, p2 = he[(v1, v2)].nxt.v2, he[(v2, v1)].nxt.v2
    he.pop((v1, v2))
    he.pop((v2, v1))
    get_triangle(p1, p2, v2, he, cache_data)
    get_triangle(p2, p1, v1, he, cache_data)
    change_cache(v1, v2, p1, p1, p2, v2, cache_data)
    change_cache(v2, v1, p2, p2, p1, v1, cache_data)


def find_triangle(p, he, cache_data):
    cache, curr_size, w, h = cache_data["cache"], cache_data["curr_size"], cache_data["w"], cache_data["h"]
    sh = h / curr_size
    sw = w / curr_size
    a, b, c = cache[int(max(0, p.x - 1) / sw)][int(max(0, p.y - 1) / sh)]
    case = triangle_predicate(a, b, c, p)
    while not case:
        for u, v in ((a, b), (b, c), (c, a)):
            w = he[(u, v)].nxt.v2
            a1, a2 = sign_area(u, v, p), sign_area(u, v, w)
            if a1 != a2 or a1 == 0:
                a, b, c = v, u, he[(v, u)].nxt.v2
                case = triangle_predicate(a, b, c, p)
                break
    return case, a, b, c


def insert_point(p, he, cache_data):
    case, a, b, c = find_triangle(p, he, cache_data)
    if case == 1:
        for u, v in ((a, b), (b, c), (c, a)):
            get_triangle(u, v, p, he, cache_data)
        change_cache(a, b, c, a, b, p, cache_data)
        for u, v in ((a, b), (b, c), (c, a)):
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


def Delaunay_triangulation(p, w, h):
    he = {}
    added = []
    curr_size = 1
    cache = [[0] * curr_size for i in range(curr_size)]
    width, height = w, h
    cache_data = {"cache": cache, "curr_size": curr_size, "w": width, "h": height, "k": 5}
    ch, other_points = ch_triangulation(p, he, cache_data)
    for pt in other_points:
        is_added = insert_point(pt, he, cache_data)
        if is_added:
            added.append(pt)

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
    return he, added + ch


def get_triangles(he):
    triangles = []
    used = {}
    for key in he:
        e1 = he[key]
        if not used.get(e1) and not e1.is_external_face:
            e2 = e1.nxt
            e3 = e2.nxt
            triangles.append(Triangle(e1))
            used[e1] = True
            used[e2] = True
            used[e3] = True
    return triangles


def quasi_random2d(n, w, h):
    seed = r()
    g = 1.32471795724474602596
    a1 = 1.0 / g
    a2 = 1.0 / (g * g)
    p = []
    for i in range(n):
        x = (seed + a1 * (i + 1)) % 1
        y = (seed + a2 * (i + 1)) % 1
        x = int(x * w)
        y = int(y * h)
        p.append(Point(x, y))
    return p


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
    for t in triangles:
        v1 = t.e.v1
        v2 = t.e.v2
        v3 = t.e.nxt.v2
        v1.color = rr(1, 3)
        v2.color = rr(1, 3)
        v3.color = rr(1, 3)


def Urquhart_graph(triangles):
    for t in triangles:
        e1 = t.e
        e2 = e1.nxt
        e3 = e2.nxt
        d = [square_of_dist(e.v1, e.v2) for e in (e1, e2, e3)]
        mn = max(d)
        (e1, e2, e3)[d.index(mn)].is_deleted = True


#w, h = 800, 800
#p = quasi_random2d(1000, w, h)
#s = dt.now()
#he, p = Delaunay_triangulation(p, w, h)
#g = get_graph(p)
#bfs(g, p[0])
#triangles = get_triangles(he)
#set_colors(triangles)
#Urquhart_graph(triangles)
#print(dt.now() - s)

#r = 5
#colors_code = {1: "red", 2: "green", 3: "blue"}
#root = Tk()
#root.geometry(str(w) + "x" + str(h))
#c = Canvas(width=w, height=h)
#c.pack()
#for key in he:
#    e = he[key]
#    v1 = e.v1
#    if not e.is_deleted and not e.twin.is_deleted:
#        c.create_line(e.v1.x, e.v1.y, e.v2.x, e.v2.y)
#        c.create_oval(v1.x - r, v1.y - r, v1.x + r, v1.y + r, outline=colors_code[v1.color], fill=colors_code[v1.color])
#root.mainloop()
