mu_xy = \(f){
    helper = \(helper, n){
        [r] = if(f(x=n).y,
            then=n,
            else=helper(helper, n + 1).r)
    },
    [return] = helper(helper, 0).r
}
main = \{
    [out] = mu_xy(\(x){
        [y] = less(x * x + 15 * x, 2 * x * x - 2 * x)
    })
}
