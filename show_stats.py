"""Show dataset statistics"""
import pandas as pd

df = pd.read_csv('data/courses_clean.csv')

print("=" * 60)
print("   DATASET SUMMARY - COURSE RECOMMENDATION SYSTEM")
print("=" * 60)

print(f"\n📚 Total cours: {len(df)}")

print(f"\n🏛️ Par plateforme:")
print(df['platform'].value_counts().to_string())

print(f"\n📁 Par categorie:")
print(df['category'].value_counts().to_string())

print(f"\n📊 Par niveau:")
print(df['level'].value_counts().to_string())

print(f"\n⭐ Rating moyen: {df['rating'].mean():.2f}")
print(f"🆓 Cours gratuits: {len(df[df['price'] == 'Free'])}")
print(f"💰 Cours payants: {len(df[df['price'] != 'Free'])}")

print("\n" + "=" * 60)
print("   DATASET READY FOR RECOMMENDATION SYSTEM!")
print("=" * 60)
