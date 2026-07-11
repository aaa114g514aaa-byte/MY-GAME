#include <iostream>
int main() {
    int a = 42, arr[] = {10,20,30};
    int* p = &a;
    std::cout << "a=" << a << " *p=" << *p << "\n";
    *p = 99;
    std::cout << "after *p=99, a=" << a << "\n";
    p = arr;
    for(int i=0;i<3;i++) std::cout << "arr["<<i<<"]=" << *(p+i) << "\n";
    int*& pref = p;
    std::cout << "ref to ptr: " << *pref << "\n";
    int* np = nullptr;
    std::cout << "nullptr: " << np << "\n";
}
