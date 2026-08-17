outer = \(n){
    [f] = \(m){
        [y] = n + m
    }
}

outer2 = \{
    [g] = \(n){
        [y] = n * 2
    }
}

main = \(a){
    [o] = outer(a).f(a).y,
    [p] = outer2.g(a).y
}
