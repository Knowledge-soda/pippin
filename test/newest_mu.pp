mu = \(f, in, out){
    helper = \(helper, n){
        [r] = if(# get(apply(f, in, n), out),
            f(l=n).return,
            then=n,
            else=helper(helper, n + 1).r)
    },
    [return] = helper(helper, 0).r
}
main = \{
    [out] = mu(apply(more, "r", 100), in="l", out="return")
}
