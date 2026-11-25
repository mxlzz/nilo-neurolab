#include <windows.h>
#include <stdint.h>
#include <string.h>
static unsigned char brain[0xc8c], norn[0x2c24], chem[0x208], concept[640*16], decision[16*16], perception[112*16], contacts[32][128*12], inc[640][12];
static void put(unsigned char *p, unsigned int offset, uintptr_t v) { uint32_t q=(uint32_t)v; memcpy(p+offset,&q,4); }
__declspec(dllexport) __declspec(noinline) void __cdecl nl_tick(unsigned char *b,unsigned char *n) { volatile unsigned int z=b[0]+n[0]; (void)z; }
int main(void) {
  unsigned int i,j,k;
  put(brain,0xa4,(uintptr_t)perception);put(brain,0xac,112);
  put(brain,0x6e4,(uintptr_t)concept);put(brain,0x6ec,640);
  put(brain,0x554,(uintptr_t)decision);put(brain,0x55c,16);
  brain[0x4da]=1;put(brain,0x568,16);
  put(norn,0x2c18,(uintptr_t)brain);put(norn,0x2c1c,(uintptr_t)chem);
  for(i=0;i<640;i++){concept[i*16+12]=1;put(concept+i*16,4,(uintptr_t)inc[i]);put(inc[i],0,(uintptr_t)(perception+(i%112)*16));inc[i][7]=128;inc[i][8]=128;inc[i][9]=5;}
  for(i=0;i<16;i++)for(j=0;j<2;j++){
    unsigned char *d=decision+i*16;unsigned char *a=contacts[i*2+j];
    d[12+j]=128;put(d,4+j*4,(uintptr_t)a);
    for(k=0;k<128;k++){put(a+k*12,0,(uintptr_t)(concept+(k%2)*16));a[k*12+9]=5;}
  }
  decision[18]=10;nl_tick(brain,norn);return 0;
}
