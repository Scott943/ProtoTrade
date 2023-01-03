from prototrade.prototrade import ProtoTrade
   
def main():
   system = ProtoTrade(num_strategies=3)
   system.test_execution()

if __name__ == "__main__":
   main()