pravokutnik = (a, b){
    [p] = *(l=a, r=b),
    t = *(l=2, r=b),
    [o] = +(l=*(l=2, r=a), r=t)
}
