#include <windows.h>
volatile unsigned int nl_sink;
__declspec(dllexport) __declspec(noinline) void __cdecl nl_tick(unsigned int value) { nl_sink=value; }
int main(void) { nl_tick(11); Sleep(100); nl_tick(22); Sleep(100); nl_tick(33); return 0; }
