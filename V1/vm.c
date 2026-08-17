#include"const_compile.c"

#define NO_BUILTINS (15)

typedef enum InstructionType {
    AD_FUNC,
    RESV,
    SET_RES,
    APPLY,
    SET_STR_ARG,
    SET_NUM_ARG,
    PROPERTY,
    ARG_NAME,
    NUM_CONST,
    STR_CONST
} InstructionType;


unsigned int read_unsigned(FILE *file){
    unsigned char data[4];
    fread(data, sizeof(unsigned char), 4, file);
    return ((unsigned int) data[0]) << 24 |
           ((unsigned int) data[1]) << 16 |
           ((unsigned int) data[2]) << 8 |
           ((unsigned int) data[3]);
}

int read_signed(unsigned char *data){
    return ((int) data[0]) << 24 |
           ((int) data[1]) << 16 |
           ((int) data[2]) << 8 |
           ((int) data[3]);
}

bool check_magic(FILE *file){
    char data[8], compare[] = "ad_hoc";
    fread(data, sizeof(char), 8, file);
    for (size_t i = 0;i < 6;i++){
        if (data[i] != compare[i])
            return false;
    }
    return data[6] == 0x30 && data[7] == 0x04;
}

char **create_const_table(unsigned int const_size, char consts[const_size]){
    size_t count = 0;
    for (size_t i = 0;i < const_size;i++){
        if (!consts[i]) count++;
    }
    char **ret = malloc(sizeof(char *) * count);
    // printf("maxcount=%zu\n", count);
    count = 0;
    ret[0] = consts;
    for (size_t i = 0;i < const_size - 1;i++){
        if (!consts[i]){
            count++;
            // printf("count=%zu\n", count);
            ret[count] = consts + i + 1;
        }
    }
    return ret;
}

void create_builtins(Node **node_list){
    node_list[0] = create_rl_built_in(sum);
    node_list[1] = create_rl_built_in(minus);
    node_list[2] = create_rl_built_in(mult);
    node_list[3] = create_rl_built_in(divide);
    node_list[4] = create_rl_built_in(less);
    node_list[5] = create_rl_built_in(more);
    node_list[6] = create_rl_built_in(equal);
    node_list[7] = create_rl_built_in(geq);
    node_list[8] = create_rl_built_in(leq);
    node_list[9] = create_ternary_built_in(if_node, "cond", "then", "else");
    node_list[10] = create_ternary_built_in(get_node, "function", "property", NULL);
    node_list[11] = create_ternary_built_in(apply_node, "function", "name", "value");
    node_list[12] = create_str_built_in(str_head);
    node_list[13] = create_str_built_in(str_tail);
    node_list[14] = create_str_built_in(str_empty);
}

size_t get_instruction_size(InstructionType type){
    switch (type){
        case AD_FUNC:
            return 0;
        case ARG_NAME:
        case STR_CONST:
        case NUM_CONST:
            return 5;
        case PROPERTY:
        case APPLY:
        case SET_NUM_ARG:
        case SET_STR_ARG:
        case SET_RES:
        case RESV:
            return 9;
    }
}

Node *load_program(FILE *file){
    if (!check_magic(file)){
        printf("Invalid file!\n");
        return NULL;
    }
    unsigned int const_size = read_unsigned(file);
    unsigned int code_size = read_unsigned(file);
    char *consts = malloc(sizeof(char) * const_size);
    fread(consts, sizeof(char), const_size, file);
    unsigned char *code = malloc(sizeof(unsigned char) * (code_size - NO_BUILTINS));
    fread(code, sizeof(unsigned char), (code_size - NO_BUILTINS), file);
    // printf("PHASE 1 %u %u!\n", const_size, code_size);

    char **c_table = create_const_table(const_size, consts);
    Node **node_list = malloc(sizeof(Node *) * code_size);
    create_builtins(node_list);
    // printf("PHASE 2!\n");

    for (size_t read_index = 0;read_index < code_size - NO_BUILTINS;){
        size_t write_index = read_index + NO_BUILTINS;
        InstructionType type = code[read_index];
        if (type == AD_FUNC){
            read_index++;
            int ret_num = read_signed(code + read_index);
            read_index += 4;
            int arg_num = read_signed(code + read_index); 
            read_index += 4;
            node_list[write_index] = create_func(arg_num, ret_num);
            for (size_t i = 0;i < arg_num;i++){
                int string = read_signed(code + read_index);
                set_func_arg(node_list[write_index], c_table[string]);
                read_index += 4;
            }
        } else {
            read_index += get_instruction_size(type);
        }
    }

    // printf("PHASE 3!\n");
    Node *current_function = NULL;
    for (size_t read_index = 0;read_index < code_size - NO_BUILTINS;){
        size_t write_index = read_index + NO_BUILTINS;
        InstructionType type = code[read_index];
        read_index += 1;
        // printf("%zu ", write_index);
        if (type == AD_FUNC){
            current_function = node_list[write_index];
            read_index += 4;
            int arg_num = read_signed(code + read_index); 
            read_index += 4 * (arg_num + 1);
            // printf("AD_FUNC ? %i\n", arg_num);
        } else if (type == ARG_NAME){
            int string = read_signed(code + read_index);
            node_list[write_index] = create_name(c_table[string]);
            read_index += 4;
            // printf("ARG_NAME %i\n", string);
        } else if (type == PROPERTY){
            int node_index = read_signed(code + read_index);
            read_index += 4;
            int string = read_signed(code + read_index);
            read_index += 4;
            node_list[write_index] = create_property(node_list[node_index],
                    c_table[string]);
            // printf("PROPERTY %i %i\n", node_index, string);
        } else if (type == NUM_CONST){
            int num = read_signed(code + read_index);
            node_list[write_index] = create_number(num);
            read_index += 4;
            // printf("NUM_CONST %i\n", num);
        } else if (type == STR_CONST){
            int string = read_signed(code + read_index);
            node_list[write_index] = create_string(c_table[string]);
            read_index += 4;
        } else if (type == APPLY){
            int node_index = read_signed(code + read_index);
            read_index += 4;
            int arg_num = read_signed(code + read_index);
            read_index += 4;
            // printf("APPLY %i %i\n", node_index, arg_num);
            node_list[write_index] = create_application(node_list[node_index], arg_num);
            for (size_t i = 0;i < arg_num;i++){
                InstructionType subtype = code[read_index];
                read_index++;
                int name = read_signed(code + read_index);
                read_index += 4;
                int res = read_signed(code + read_index);
                read_index += 4;
                if (subtype == SET_STR_ARG){
                    set_appl_arg_str(node_list[write_index], c_table[name], node_list[res]);
                } else if (subtype == SET_NUM_ARG){
                    set_appl_arg_num(node_list[write_index], name, node_list[res]);
                }
            }
        } else if (type == SET_RES){
            int name = read_signed(code + read_index);
            read_index += 4;
            int node_index = read_signed(code + read_index);
            read_index += 4;
            // printf("SET_RES %i %i\n", name, node_index);
            set_func_res(current_function, c_table[name], node_list[node_index]);
        }
    }
    // printf("PHASE 4!\n");

    Node *res = node_list[NO_BUILTINS];

    free(node_list);
    free(code);
    free(c_table);

    return res;
}


int main(int argc, char *argv[]){
    if (argc <= 1){
        printf("Insufficent arguments\n");
        return 1;
    }
    FILE *file = fopen(argv[1], "rb");
    if (!file){
        printf("Couldn't open file '%s'\n", argv[1]);
        return 1;
    }
    Node *main = load_program(file);
    fclose(file);
    if (main){
        driver(main);
    } else {
        printf("Error occured while reading file '%s'\n", argv[1]);
    }
    return 0;
}
