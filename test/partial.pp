f = \(a, b){
    [y] = a + b
}
twice = \(f, x){
    [return] = f(a=f(a=x).y).y
}
main = \(n){
    [out] = twice(f(b=12), n)
}
