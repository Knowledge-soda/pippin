main = \(a, b){
    l = 5,
    squared = \(x){
        [s] = x * x + l
    },
    [out] = squared(a).s + squared(b).s + squared(a + b).s
}
