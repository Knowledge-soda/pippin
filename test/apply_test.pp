f = \(x, y, z){
    [out1] = x + y,
    [w] = x * y,
    [out2] = y + z * z
}

main = \(v_in, v_out){
    [out] = get(apply(f(y=5), v_in, 10), v_out)
}
