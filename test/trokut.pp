pravokutnik = (a, b){
    [p] = *(l=a, r=b),
    t = *(l=2, r=b),
    [o] = +(l=*(l=2, r=a), r=t)
}

trokut = (a, b){
    t = pravokutnik(a=a, b=b).p,
    [p] = /(l=tt, r=2)
}
