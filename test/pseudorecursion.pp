f = (x){
    [a] = g(y=x + 1).a,
    [b] = x * x,
    [c] = f(x=x + 1).b
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
