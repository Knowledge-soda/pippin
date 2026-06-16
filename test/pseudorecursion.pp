f = (x){
    [a] = g(y=+(l=x, r=1)).a,
    [b] = *(l=x, r=x),
    [c] = f(x=+(l=x, r=1)).b
}

g = (y){
    [a] = f(x=y).b
}

h = (x){
    [o] = h(x=x).o
}

main = (x){
    [out] = f(x=x).c,
    [out2] = h(x=x).o
}
