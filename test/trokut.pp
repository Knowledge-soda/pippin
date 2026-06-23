pravokutnik = (a, b){
    [p] = a * b,
    t = 2 * b,
    [o] = 2 * a + t
}

trokut = (a, b){
    t = pravokutnik(a=a),
    tt = t(b=b).p,
    [p] = tt / 2
}

main = (a, b){
    p = pravokutnik(a=a, b=b),
    [ops] = p.o,
    [prav_povr] = p.p,
    [trok] = trokut(a=a, b=b).p
}
