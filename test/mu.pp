_mu_xy = \(f, n){
    [return] = if(f(x=n).y,
        then=n,
        else=_mu_xy(f, n + 1))
}
mu_xy = \(f){
    [return] = _mu_xy(f, 0)
}
limit = \(x){
    [y] = less(x * x + 15 * x, 2 * x * x - 2 * x)
}
main = \{
    [out] = mu_xy(limit)
}
